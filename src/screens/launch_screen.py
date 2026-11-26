import time
from panda3d.core import ClockObject
from logger import Logger, load_experiment_config
from screens.screen import Screen
from view.heart_scene import HeartScene


class LaunchScreen(Screen):
    # the heart scene with eye tracking, what the old controller.py did

    def __init__(self, app):
        super().__init__(app)
        config = app.app_config
        self.camera_offset_y_cm = config["camera_offset_y_cm"]

        self.scene = HeartScene(
            app,
            config["screen_width_cm"],
            config["screen_height_cm"],
            config["camera_offset_y_cm"]
        )

        self.logger = None
        self.experiment_config = None
        self.selected_smoothing = None
        self.clock = ClockObject.getGlobalClock()

    def show(self):
        super().show()
        config = self.app.app_config

        self.scene.set_head_position((0, -self.camera_offset_y_cm, 60))
        self.scene.show()

        if config["logging_enabled"]:
            self.experiment_config = load_experiment_config()
            self.logger = Logger(config, self.experiment_config)

        self.selected_smoothing = None
        self.app.tracking.set_logger(self.logger)
        self.app.tracking.start()

        self.accept(config['smoothing']['cycle_key'], self.app.tracking.cycle_smoothing)
        self.accept("escape", self.app.switch_to, ["menu"])
        self.app.taskMgr.add(self.update_view, "receive_tracking", sort=-10)

    def hide(self):
        super().hide()
        self.app.taskMgr.remove("receive_tracking")
        self.app.tracking.stop()
        self.app.tracking.set_logger(None)
        self.scene.hide()
        self.save_log()

    def save_log(self):
        if self.logger is None:
            return

        if self.logger.is_done():
            self.logger.save()
        else:
            print("experiment abrupted, nothing saved")
        self.logger = None

    def update_view(self, task):
        result = self.app.tracking.get_result()

        if result is not None:
            position, face_found, timestamp, smoothing_name = result

            if smoothing_name != self.selected_smoothing:
                self.selected_smoothing = smoothing_name
                self.scene.show_smoothing_popup(smoothing_name, self.app.app_config['smoothing']['popup_seconds'])

            if face_found and position is not None:
                self.scene.set_head_position(position)

            if self.logger is not None:
                if self.logger.is_measuring():
                    frame_ms = self.clock.getDt() * 1000
                    data_age_ms = time.monotonic() * 1000 - timestamp
                    self.logger.add_render_row(frame_ms, data_age_ms, face_found)

                elif self.logger.is_done() and self.experiment_config["close_when_done"]:
                    # back to the menu instead of closing the whole program
                    self.app.switch_to("menu")
                    return task.done

        return task.cont
