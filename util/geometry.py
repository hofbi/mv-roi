"""Geometric Operations"""

from shapely.geometry import Point
import shapely.affinity


def shift_label_points(label_data, x, y):
    """
    Shift all label points by x and y
    :param label_data:
    :param x:
    :param y:
    :return:
    """
    for shape in label_data["shapes"]:
        circle = Circle.from_json(shape["points"])
        circle.translate(x, y)
        shape["points"] = circle.to_json()

    return label_data


def is_shape_inside(shape, layout_model):
    """
    Check if the shapes center is inside the provided model
    :param shape:
    :param layout_model:
    :return:
    """
    centroid = shape["points"][0]
    return layout_model.is_inside(centroid[0], centroid[1])


class Circle:
    """Circular ROI Element"""

    IMAGE_ORIGIN = Point(0, 0)

    def __init__(self, center, point_on_radius):
        self.__centroid = Point(center[0], center[1])
        self.__radius_point = Point(point_on_radius[0], point_on_radius[1])

    @staticmethod
    def from_region_props(region):
        return Circle(
            (region.centroid[1], region.centroid[0]),
            (region.centroid[1] + region.equivalent_diameter / 2, region.centroid[0]),
        )

    @staticmethod
    def from_json(json_points):
        return Circle(json_points[0], json_points[1])

    def to_json(self):
        return [
            [self.__centroid.x, self.__centroid.y],
            [self.__radius_point.x, self.__radius_point.y],
        ]

    @property
    def centroid(self):
        return self.__centroid

    @property
    def bounding_box(self):
        circle = self.centroid.buffer(self.centroid.distance(self.__radius_point))
        return list(circle.bounds)

    def translate(self, x, y):
        self.__centroid = shapely.affinity.translate(self.__centroid, x, y)
        self.__radius_point = shapely.affinity.translate(self.__radius_point, x, y)

    def scale(self, x_scale, y_scale):
        self.__centroid = shapely.affinity.scale(
            self.__centroid, x_scale, y_scale, origin=self.IMAGE_ORIGIN
        )
        self.__radius_point = shapely.affinity.scale(
            self.__radius_point, x_scale, y_scale, origin=self.IMAGE_ORIGIN
        )
