import time
from panda3d.core import ClockObject
from logger import Logger, load_experiment_config
from model.eyetracker import open_config
from tracking import TrackingService
from view.scene_manager import HeartApp

def main():
    config = open_config()

    # screen values are in config.json now
    screen_width_cm = config["screen_width_cm"]
    screen_height_cm = config["screen_height_cm"]
    camera_offset_y_cm = config["camera_offset_y_cm"]

    logger = None
    experiment_config = None
    if config["logging_enabled"]:
        experiment_config = load_experiment_config()
        logger = Logger(config, experiment_config)

    tracking = TrackingService(config, logger)

    app = HeartApp(
        screen_width_cm,
        screen_height_cm,
        camera_offset_y_cm
    )

    app.set_head_position((0, -camera_offset_y_cm, 60))
    app.accept(config['smoothing']['cycle_key'], tracking.cycle_smoothing)
    selected_smoothing = None
    clock = ClockObject.getGlobalClock()
    
    def update_view(task):
        nonlocal selected_smoothing
        result = tracking.get_result()

        if result is not None:
            position, face_found, timestamp, smoothing_name = result

            if smoothing_name != selected_smoothing:
                selected_smoothing = smoothing_name
                app.show_smoothing_popup(smoothing_name, config['smoothing']['popup_seconds'])

            if face_found and position is not None:
                app.set_head_position(position)

            if logger is not None:
                if logger.is_measuring():
                    frame_ms = clock.getDt() * 1000
                    data_age_ms = time.monotonic() * 1000 - timestamp
                    logger.add_render_row(frame_ms, data_age_ms, face_found)

                elif logger.is_done() and experiment_config["close_when_done"]:
                    app.userExit()

        return task.cont

    app.taskMgr.add(update_view, "receive_tracking", sort=-10)

    tracking.start()
    app.accept("escape", app.userExit)

    try:
        app.run()

    finally:
        tracking.stop()

        if logger is not None:
            if logger.is_done():
                logger.save()
            else:
                print("experiment abrupted, nothing saved")

        app.destroy()

if __name__ == '__main__':
    main()
