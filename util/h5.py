"""Module for h5 operations"""

import json
from pathlib import Path
from typing import List

import h5py
import PIL.Image
from tqdm import tqdm

from util import config
from util.files import write_json


class HDF5Wrapper:
    """HDF5 File Wrapper"""

    SAMPLE_KEY = "sample"
    IMAGE_KEY = "image"
    ROI_KEY = "roi"

    def __init__(self, file_path: Path, mode: str):
        self.__h5_file = h5py.File(file_path, mode)

    def __del__(self):
        self.__h5_file.close()

    @staticmethod
    def get_or_create_group(root, key: str):
        if key in root:
            return root[key]
        else:
            return root.create_group(key)

    @staticmethod
    def sample_key(index: int) -> str:
        return f"{HDF5Wrapper.SAMPLE_KEY}{index:06d}"

    @staticmethod
    def index(sample_key: str) -> int:
        return int(sample_key.lstrip(HDF5Wrapper.SAMPLE_KEY))

    @property
    def h5_file(self):
        return self.__h5_file


class HDF5Writer:
    """HDF5 File Writer"""

    def __init__(self, file_path: Path):
        self.__h5_file = HDF5Wrapper(file_path, "w")

    def add_image_group(self, index: int, merge_group):
        self.__add_merge_group(
            index, HDF5Wrapper.IMAGE_KEY, merge_group, PIL.Image.open
        )

    def add_roi_group(self, index: int, merge_group):
        def read_json_string(path: Path):
            return path.read_text()

        self.__add_merge_group(
            index,
            HDF5Wrapper.ROI_KEY,
            merge_group,
            read_json_string,
            h5py.string_dtype(),
        )

    def __add_merge_group(self, index, key, merge_group, data_reader, d_type=None):
        group = HDF5Wrapper.get_or_create_group(
            self.__h5_file.h5_file, HDF5Wrapper.sample_key(index)
        )
        sub_group = HDF5Wrapper.get_or_create_group(group, key)
        for topic in merge_group.keys:
            file_path = merge_group.get_file_path_by_key(topic)
            sub_group.create_dataset(topic, data=data_reader(file_path), dtype=d_type)


class HDF5Extractor:
    """HDF5 File Extractor"""

    def __init__(self, file_path: Path):
        self.__h5_file = HDF5Wrapper(file_path, "r")

    def extract_data(self, output_dir: Path):
        output_path = output_dir / Path(self.__h5_file.h5_file.filename).stem
        output_path.mkdir(parents=True, exist_ok=True)
        for sample in tqdm(self.__h5_file.h5_file.items()):
            index = HDF5Wrapper.index(sample[0])
            roi_data = self.get_roi_data(sample[1][HDF5Wrapper.ROI_KEY], index)
            for json_data, target in roi_data:
                write_json(output_path / target, json_data)
            image_file_name = [json_data["imagePath"] for json_data, _ in roi_data]
            image_data = self.get_image_data(sample[1][HDF5Wrapper.IMAGE_KEY])
            for image, target in zip(image_data, image_file_name):
                image.save(output_path / target)

    @staticmethod
    def file_name(key: str, index: int, suffix: str) -> str:
        return config.MVROI_FILENAME_TEMPLATE % (key, index, suffix)

    @staticmethod
    def get_image_data(data) -> List:
        image_data = []
        for key in data.keys():
            array = data[key][:]
            image = PIL.Image.fromarray(array.astype("uint8"), config.IMAGE_FORMAT)
            image_data.append(image)
        return image_data

    @staticmethod
    def get_roi_data(data, index: int) -> List:
        return [
            (
                json.loads(data[key][()]),
                HDF5Extractor.file_name(key, index, config.LABELME_SUFFIX),
            )
            for key in data.keys()
        ]
