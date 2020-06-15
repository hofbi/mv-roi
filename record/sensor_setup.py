"""
This module contains the camera manager for recording a multi camera setup
"""

import weakref
from configparser import ConfigParser

import carla
from carla import ColorConverter as cc

try:
    import pygame
except ImportError:
    raise RuntimeError("cannot import pygame, make sure pygame package is installed")

try:
    import numpy as np
except ImportError:
    raise RuntimeError("cannot import numpy, make sure numpy package is installed")


class CameraManager:
    """Camera Manager"""

    def __init__(self, parent_actor, hud, config_file):
        self.sensor = None
        self.non_active_sensors = []
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        self._parser = ConfigParser()
        self._parser.read(config_file)

        self._camera_transforms = [
            self._get_camera_transform_from_config(camera)
            for camera in self._parser.sections()
        ]
        self.sensors = [
            ["sensor.camera.rgb", cc.Raw, camera, (self.hud.dim[0], self.hud.dim[1])]
            for camera in self._parser.sections()
        ]
        self._record_time = {
            camera: self.hud.simulation_time for camera in self._parser.sections()
        }
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            blue_print = bp_library.find(item[0])
            if item[0].startswith("sensor.camera"):
                blue_print.set_attribute("image_size_x", str(hud.dim[0]))
                blue_print.set_attribute("image_size_y", str(hud.dim[1]))
            item.append(blue_print)
        self.index = None

    def _get_camera_transform_from_config(self, key):
        return (
            carla.Transform(
                carla.Location(
                    x=float(self._parser.get(key, "x")),
                    y=float(self._parser.get(key, "y")),
                    z=float(self._parser.get(key, "z")),
                ),
                carla.Rotation(yaw=int(self._parser.get(key, "yaw"))),
            ),
            carla.AttachmentType.Rigid,
        )

    def set_sensor(self, index, notify=True, force_respawn=False):
        index = index % len(self.sensors)
        needs_respawn = (
            True
            if self.index is None
            else (
                force_respawn or (self.sensors[index][2] != self.sensors[self.index][2])
            )
        )
        self.index = index
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[index][0],
                attach_to=self._parent,
                attachment_type=self._camera_transforms[index][1],
            )
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(
                lambda image: CameraManager._parse_image(
                    weak_self, self.sensors[index][2], image
                )
            )
        if notify:
            self.hud.notification(self.sensors[index][2])

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self._record_time = dict.fromkeys(self._record_time, self.hud.simulation_time)
        self.hud.notification("Recording %s" % ("On" if self.recording else "Off"))
        if self.recording:
            self._record_non_active_sensors()
        else:
            self._destroy_non_active_sensors()

    def _record_non_active_sensors(self):
        self._destroy_non_active_sensors()
        for idx, _ in enumerate(self.sensors):
            if idx != self.index:
                self.non_active_sensors.append(
                    self._parent.get_world().spawn_actor(
                        self.sensors[idx][-1],
                        self._camera_transforms[idx][0],
                        attach_to=self._parent,
                        attachment_type=self._camera_transforms[idx][1],
                    )
                )
        weak_self = weakref.ref(self)
        self.non_active_sensors[0].listen(
            lambda image: CameraManager._record_image(
                weak_self, self.sensors[1][2], image
            )
        )
        self.non_active_sensors[1].listen(
            lambda image: CameraManager._record_image(
                weak_self, self.sensors[2][2], image
            )
        )
        self.non_active_sensors[2].listen(
            lambda image: CameraManager._record_image(
                weak_self, self.sensors[3][2], image
            )
        )
        self.non_active_sensors[3].listen(
            lambda image: CameraManager._record_image(
                weak_self, self.sensors[4][2], image
            )
        )
        self.non_active_sensors[4].listen(
            lambda image: CameraManager._record_image(
                weak_self, self.sensors[5][2], image
            )
        )

    def _destroy_non_active_sensors(self):
        if not self.non_active_sensors:
            for sensor in self.non_active_sensors:
                sensor.destroy()
            del self.non_active_sensors[:]
            self.non_active_sensors = []

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, name, image):
        self = weak_self()
        if not self:
            return
        image.convert(self.sensors[self.index][1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if (
            self.recording and self.hud.simulation_time - self._record_time[name] > 0.1
        ):  # Log every 100ms
            self._record_time[name] = self.hud.simulation_time
            image.save_to_disk("_out/%s-%08d" % (name, image.frame))

    @staticmethod
    def _record_image(weak_self, name, image):
        self = weak_self()
        if not self:
            return
        if (
            self.recording and self.hud.simulation_time - self._record_time[name] > 0.1
        ):  # Log every 100ms
            self._record_time[name] = self.hud.simulation_time
            image.save_to_disk("_out/%s-%08d" % (name, image.frame))
