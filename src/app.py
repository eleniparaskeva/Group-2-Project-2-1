import time
import simplepbr
from direct.showbase.ShowBase import ShowBase
from panda3d.core import ClockObject
from logger import Logger, load_experiment_config
from model.eyetracker import open_config
from tracking import TrackingService
from view.heart_scene import HeartScene


class App(ShowBase):

    def __init__(self, config):
        super().__init__()

        self.app_config = config

        self.disableMouse() #makes sure mouse does not override parallax effect
        self.camLens.setNearFar(1, 1000) #how far from the camera does panda start and stop drawing set to cm
        simplepbr.init()

        # screen values are in config.json now
        self.screen_width_cm = config["screen_width_cm"]
        self.screen_height_cm = config["screen_height_cm"]
        self.camera_offset_y_cm = config["camera_offset_y_cm"]

        self.logger = None
        self.experiment_config = None
        if config["logging_enabled"]:
            self.experiment_config = load_experiment_config()
            self.logger = Logger(config, self.experiment_config)

        self.tracking = TrackingService(config, self.logger)

        self.scene = HeartScene(
            self,
            self.screen_width_cm,
            self.screen_height_cm,
            self.camera_offset_y_cm
        )
        self.scene.set_head_position((0, -self.camera_offset_y_cm, 60))

        self.selected_smoothing = None
        self.clock = ClockObject.getGlobalClock()

        self.accept(config['smoothing']['cycle_key'], self.tracking.cycle_smoothing)
        self.accept("escape", self.userExit)
        self.taskMgr.add(self.update_view, "receive_tracking", sort=-10)

        self.scene.show()
        self.tracking.start()

    def update_view(self, task):
        result = self.tracking.get_result()

        if result is not None:
            position, face_found, timestamp, smoothing_name = result

            if smoothing_name != self.selected_smoothing:
                self.selected_smoothing = smoothing_name
                self.scene.show_smoothing_popup(smoothing_name, self.app_config['smoothing']['popup_seconds'])

            if face_found and position is not None:
                self.scene.set_head_position(position)

            if self.logger is not None:
                if self.logger.is_measuring():
                    frame_ms = self.clock.getDt() * 1000
                    data_age_ms = time.monotonic() * 1000 - timestamp
                    self.logger.add_render_row(frame_ms, data_age_ms, face_found)

                elif self.logger.is_done() and self.experiment_config["close_when_done"]:
                    self.userExit()

        return task.cont

    def close_app(self):
        # called once when the window closes (not named shutdown, ShowBase already has a shutdown method)
        self.tracking.stop()

        if self.logger is not None:
            if self.logger.is_done():
                self.logger.save()
            else:
                print("experiment abrupted, nothing saved")


def main():
    config = open_config()
    app = App(config)

    try:
        app.run()

    finally:
        app.close_app()
        app.destroy()

if __name__ == '__main__':
    main()
