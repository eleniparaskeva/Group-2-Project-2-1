import threading
import time
from panda3d.core import ClockObject
from logger import Logger, load_experiment_config
from queue import SimpleQueue, Empty
from eyetracker import EyeTracker, open_config
from scene_manager import HeartApp

result_lock = threading.Lock()
latest_result = None
stop_tracking = threading.Event()
smoothing_commands = SimpleQueue()

def eye_tracking(config, logger):
    global latest_result
    tracker = None

    try:
        tracker = EyeTracker(config)

        while not stop_tracking.is_set():
            # Only the tracking thread changes filter state.
            while True:
                try:
                    smoothing_commands.get_nowait()
                except Empty:
                    break
                tracker.smoothing.cycle()
            if not tracker.update():
                break

            if logger is not None and logger.is_measuring():
                logger.add_tracking_row(
                    tracker.face_found,
                    tracker.times,
                    tracker.raw_position,
                    tracker.z_hvid,
                    tracker.z_ipd,
                    tracker.position,
                    tracker.smoothing.name
                )

            if config["show_visualization"]:
                tracker.visualize()

            result = (*tracker.get_result(), tracker.smoothing.name)

            with result_lock:
                latest_result = result

    except Exception as error:
        print("Eye tracking error:", error)

    finally:
        if tracker is not None:
            tracker.close()

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

    app = HeartApp(
        screen_width_cm,
        screen_height_cm,
        camera_offset_y_cm
    )

    app.set_head_position((0, -camera_offset_y_cm, 60))
    app.accept(config['smoothing']['cycle_key'], smoothing_commands.put, ['cycle'])
    selected_smoothing = None
    clock = ClockObject.getGlobalClock()
    
    def update_view(task):
        nonlocal selected_smoothing
        with result_lock:
            result = latest_result

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

    tracking_thread = threading.Thread(
        target=eye_tracking,
        args=(config, logger),
        daemon=True
    )

    tracking_thread.start()
    app.accept("escape", app.userExit)

    try:
        app.run()

    finally:
        stop_tracking.set()
        tracking_thread.join(timeout=5)

        if logger is not None:
            if logger.is_done():
                logger.save()
            else:
                print("experiment abrupted, nothing saved")

        app.destroy()

if __name__ == '__main__':
    main()
