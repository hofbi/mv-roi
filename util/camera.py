"""Camera related operations"""

import math
import copy
from typing import List
from util.geometry import Circle


def calculate_angle_of_translated_roi(circle, fov, image_width):
    """Project the ROI to get the angle in current camera"""
    return math.atan(
        circle.centroid.x
        * math.sin(fov)
        / (image_width + circle.centroid.x * (math.cos(fov) - 1))
    )


def calculate_distance_to_translated_roi(
    circle, theta, fov, image_width, translation_angle
):
    """Add the shift angle according to the configuration and then project to shifted ROI"""
    return (
        image_width
        * math.tan(theta + translation_angle)
        / (
            math.tan(theta + translation_angle)
            + math.sin(fov)
            - math.cos(fov) * math.tan(theta + translation_angle)
        )
        - circle.centroid.x
    )


class RegionOverlap:
    """Create Region Overlap class"""

    BIAS = 0.93

    def __init__(
        self,
        position_camera_first: float,
        position_camera_second: float,
        fov: float,
    ):
        self.__position_camera_first = position_camera_first
        self.__position_camera_second = position_camera_second
        self.__fov = fov

    @property
    def is_valid(self) -> bool:
        """
        Judge if there is overlap between two views
        """
        return abs(self.angle_diff_between_both_views) < self.__fov

    @property
    def angle_diff_between_both_views(self) -> float:
        """
        Calculate the difference of angle of two views
        """
        angle_diff = self.__position_camera_first - self.__position_camera_second
        return self.__fix_angle_range(angle_diff)

    def __fix_angle_range(self, angle: float) -> float:
        if angle >= math.pi:
            return angle - 2 * math.pi
        if angle < -math.pi:
            return angle + 2 * math.pi
        return angle


class RoiView:
    """Camera view that contains ROIs"""

    def __init__(
        self,
        rois: List[Circle],
        camera_position: float,
        image_width: float,
        iou_threshold: float,
        fov: float,
    ) -> None:
        self.__rois = rois
        self.__camera_position = camera_position
        self.__image_width = image_width
        self.__iou_threshold = iou_threshold
        self.__fov = fov

    @property
    def position(self) -> float:
        return self.__camera_position

    @property
    def fov(self) -> float:
        return self.__fov

    @property
    def rois(self) -> List[Circle]:
        return self.__rois

    def insert(self, roi: Circle) -> None:
        """Insert roi into the list if it does not exist"""
        if not self.exists(roi) and self.is_inside(roi):
            self.__rois.append(roi)

    def is_inside(self, roi: Circle) -> bool:
        """Check if the roi locate out of the image"""
        return roi.centroid.x < self.__image_width and roi.centroid.x > 0

    def exists(self, roi: Circle) -> bool:
        """Check if the roi already exists within this view"""
        return any(
            [
                roi.iou(existing_roi) > self.__iou_threshold
                for existing_roi in self.__rois
            ]
        )

    def translate_rois(self, translation_angle: float) -> List[Circle]:
        """Translate ROIs horizontally by the specified angle"""
        circle_list = copy.deepcopy(self.__rois)
        for circle in circle_list:
            theta = calculate_angle_of_translated_roi(
                circle, self.__fov, self.__image_width
            )
            translation_x = calculate_distance_to_translated_roi(
                circle, theta, self.__fov, self.__image_width, translation_angle
            )
            circle.translate(translation_x, 0)
        return circle_list


class RoiViewPair:
    """Pair of RoiViews"""

    def __init__(self, left_view: RoiView, right_view: RoiView) -> None:
        self.left_view = left_view
        self.right_view = right_view

    def sync_rois_between_views(self) -> None:
        """Complete the missing ROI to each other"""
        overlap = RegionOverlap(
            self.left_view.position, self.right_view.position, self.left_view.fov
        )
        if overlap.is_valid:
            angle_diff = overlap.angle_diff_between_both_views * overlap.BIAS
            candidate_rois_right = self.left_view.translate_rois(angle_diff)
            candidate_rois_left = self.right_view.translate_rois(-angle_diff)
            for circle in candidate_rois_left:
                self.left_view.insert(circle)
            for circle in candidate_rois_right:
                self.right_view.insert(circle)
