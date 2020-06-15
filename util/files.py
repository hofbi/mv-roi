"""Module for file operations and models"""

import json
import re
from pathlib import Path
import os
from collections import namedtuple
from tqdm import tqdm
from util import config


PathPair = namedtuple("PathPair", ["source", "target"])


def get_files_with_suffix(input_dir, suffix, ignore=r"(?!x)x"):
    """
    Get absolute files paths from input dir matching the suffix
    :param input_dir:
    :param suffix:
    :param ignore: By default nothing should be ignored
    Never match regex from: https://stackoverflow.com/a/1845097/3883569
    :return:
    """
    path_list = os.listdir(input_dir)
    path_list.sort()
    files = [
        Path(input_dir).joinpath(file_path)
        for file_path in path_list
        if file_path.endswith(suffix) and not re.compile(ignore).match(str(file_path))
    ]
    return files


def read_json(filename):
    """
    Read json data from file
    :param filename:
    :return:
    """
    with open(filename) as json_file:
        return json.load(json_file)


def write_json(filename, json_data):
    """
    Write json data to file
    :param filename:
    :param json_data:
    :return:
    """
    with open(filename, "w") as outfile:
        json.dump(json_data, outfile)


class FileModel:
    """File Model"""

    def __init__(self, file_path):
        self.__file_path = Path(file_path)
        try:
            name_split = re.split(r"([_\-]\d+)", self.__file_path.name)
            self.__topic_name = name_split[0]
            self.__index = int(name_split[1][1:])
        except IndexError:
            raise ValueError("Invalid Filename format -> Should be KEY_INDEX.SUFFIX")

    def __lt__(self, other):
        return self.file_index < other.file_index

    @property
    def file_path(self):
        return self.__file_path

    @property
    def topic_name(self):
        return self.__topic_name

    @property
    def file_index(self):
        return self.__index

    def get_file_name_with_sequence_index(self, sequence_index, target_suffix=None):
        suffix = self.file_path.suffix if target_suffix is None else target_suffix
        return config.BDDA_FILENAME_TEMPLATE % (sequence_index, self.file_index, suffix)

    def get_file_name_with_view_key(self, view_key=None, file_index=None):
        if view_key is None:
            view_key = self.topic_name
        if file_index is None:
            file_index = self.file_index
        return config.MVROI_FILENAME_TEMPLATE % (
            view_key,
            file_index,
            self.file_path.suffix,
        )


class ImageLayoutModel:
    """Image Layout Model"""

    def __init__(self, image_layout):
        self.__image_layout = image_layout

    @staticmethod
    def create(topic, x, y, width, height):
        return ImageLayoutModel(
            {
                "camera": topic,
                "location": {"x": x, "y": y, "width": width, "height": height},
            }
        )

    @property
    def image_layout(self):
        return self.__image_layout

    @property
    def key(self):
        return self.__image_layout["camera"]

    @property
    def top_left(self):
        return (
            self.x,
            self.y,
        )

    @property
    def x(self):
        return self.__image_layout["location"]["x"]

    @property
    def y(self):
        return self.__image_layout["location"]["y"]

    @property
    def width(self):
        return self.__image_layout["location"]["width"]

    @property
    def height(self):
        return self.__image_layout["location"]["height"]

    @property
    def box(self):
        return (
            self.x,
            self.y,
            self.x + self.__image_layout["location"]["width"],
            self.y + self.__image_layout["location"]["height"],
        )

    def is_inside(self, x, y):
        return self.x < x < self.box[2] and self.y < y < self.box[3]


class MergeGroup:
    """Files that should be merged together with respect to the provided layout"""

    def __init__(self, layout, files_dict):
        self.__layout = layout
        self.__files = files_dict
        assert self.keys == list(files_dict.keys())

    @property
    def width(self):
        return self.__layout["width"]

    @property
    def height(self):
        return self.__layout["height"]

    @property
    def image_layouts(self):
        return [ImageLayoutModel(cam) for cam in self.__layout["layout"]]

    @property
    def keys(self):
        return [cam.key for cam in self.image_layouts]

    def get_file_path_by_key(self, key):
        return self.__files[key].file_path


class FileReindexer:
    """Group files for reindexing by index and reindex"""

    def __init__(self, files, keys):
        file_groups = self.group_files_by_index(files)
        (
            self.__files_to_reindex,
            self.__files_to_remove,
        ) = self.filter_files_for_reindexing(file_groups, keys)

    @staticmethod
    def group_files_by_index(files):
        file_models = [FileModel(file) for file in files]
        file_models.sort()
        file_groups = {}
        for file in file_models:
            if file.file_index in file_groups.keys():
                file_groups[file.file_index].append(file)
            else:
                file_groups[file.file_index] = [file]
        return file_groups

    @property
    def files_to_reindex(self):
        return self.__files_to_reindex

    @property
    def files_to_remove(self):
        return self.__files_to_remove

    @staticmethod
    def filter_files_for_reindexing(file_groups: {FileModel}, keys):
        files_to_reindex = []
        files_to_remove = []
        for val in file_groups.values():
            if set(file.topic_name for file in val) == set(keys):
                files_to_reindex.append(val)
            else:
                files_to_remove.append(val)
        return files_to_reindex, files_to_remove

    def clean_up(self):
        for group in self.__files_to_remove:
            for file in group:
                file.file_path.unlink()
        self.__files_to_remove = []

    def reindex(self):
        for index, group in tqdm(enumerate(self.__files_to_reindex)):
            for file in group:
                new_file_path = file.file_path.parent.joinpath(
                    file.get_file_name_with_view_key(file_index=index)
                )
                file.file_path.rename(new_file_path)


class FileGrouper:
    """Group files for merging by keys"""

    def __init__(self, layout_data, files, keys):
        self.__merge_groups = []
        self.__layout = layout_data
        file_groups = self.group_files_by_keys(files, keys)
        self.__valid = self.is_consecutive(file_groups) and self.has_same_lengths(
            file_groups
        )
        self.__build_merge_groups(file_groups)

    @staticmethod
    def group_files_by_keys(files, keys):
        file_models = [FileModel(file) for file in files]
        file_models.sort()
        file_groups = {key: [] for key in keys}
        for file in file_models:
            if file.topic_name in keys:
                file_groups[file.topic_name].append(file)
        return file_groups

    @staticmethod
    def pop_first_of_group(file_groups):
        group = {}
        for key, value in file_groups.items():
            group[key] = value.pop(0)
        return group

    @staticmethod
    def is_consecutive(file_groups):
        results = []
        for file_models in file_groups.values():
            file_numbers = [file.file_index for file in file_models]
            results.append(file_numbers == list(range(len(file_models))))

        return all(results)

    @staticmethod
    def is_empty(file_groups):
        return all([not element for element in file_groups.values()])

    def __build_merge_groups(self, file_groups):
        if not self.is_valid:
            return

        while next(iter(file_groups.values())):
            files_dict = self.pop_first_of_group(file_groups)
            self.__merge_groups.append(MergeGroup(self.__layout, files_dict))

    @staticmethod
    def has_same_lengths(file_groups):
        results = [len(file_models) for file_models in file_groups.values()]
        return len(results) > 0 and all(elem == results[0] for elem in results)

    @property
    def merge_groups(self):
        return self.__merge_groups

    @property
    def is_valid(self):
        return self.__valid


class ScenarioGrouper:
    """Group files for a scenario"""

    def __init__(
        self, scenario_index, scenario_name, image_topics, image_files, json_files=None
    ):
        self.__scenario_name = scenario_name
        self.__scenario_index = scenario_index
        self.__image_topics = image_topics
        self.__image_groups = FileGrouper.group_files_by_keys(image_files, image_topics)
        self.__json_groups = None
        self.__valid = FileGrouper.is_consecutive(
            self.__image_groups
        ) and FileGrouper.has_same_lengths(self.__image_groups)
        if json_files is not None:
            self.__json_groups = FileGrouper.group_files_by_keys(
                json_files, image_topics
            )
            self.__valid &= FileGrouper.is_consecutive(
                self.__json_groups
            ) and FileGrouper.has_same_lengths(self.__json_groups)

    @property
    def is_valid(self):
        return self.__valid

    @property
    def scenario_name(self):
        return self.__scenario_name

    @property
    def scenario_index(self):
        return self.__scenario_index

    @property
    def image_topics(self):
        return self.__image_topics

    @property
    def image_groups(self):
        return self.__image_groups

    @property
    def json_groups(self):
        return self.__json_groups

    def get_sequence_index_for_topic(self, topic):
        return "%d%d" % (self.scenario_index, self.image_topics.index(topic))

    def get_naming_data_for_topic(self, topic):
        if topic not in self.image_topics:
            raise ValueError("Topic not existing in this group")
        return {
            "view": topic,
            "scenario_name": self.scenario_name,
            "scenario_index": self.scenario_index,
        }

    def get_prepared_path_pairs(self, file_groups, output_dir, target_suffix=None):
        image_path_pairs = []
        for topic in self.image_topics:
            sequence_index = self.get_sequence_index_for_topic(topic)
            if file_groups:
                for file_model in file_groups[topic]:
                    target = Path(output_dir).joinpath(
                        file_model.get_file_name_with_sequence_index(
                            sequence_index, target_suffix
                        )
                    )
                    image_path_pairs.append(PathPair(file_model.file_path, target))

        return image_path_pairs
