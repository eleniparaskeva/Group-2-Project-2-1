import threading
from eyetracker import EyeTracker, open_config
from scene_manager import HeartApp

result_lock = threading.Lock()
latest_result = None
stop_tracking = threading.Event()

def eye_tracking(config):
    global latest_result
    tracker = None

    try:
        tracker = EyeTracker(config)

        while not stop_tracking.is_set():
            if not tracker.update():
                break

            if config["show_visualization"]:
                tracker.visualize()

            result = tracker.get_result()

            with result_lock:
                latest_result = result

    except Exception as error:
        print("Eye tracking error:", error)

    finally:
        if tracker is not None:
            tracker.close()

def main():
    config = open_config()

    # values are different for each screen
    screen_width_cm = 34.5
    screen_height_cm = 19.4
    camera_offset_y_cm = 10.7 

    app = HeartApp(
        screen_width_cm,
        screen_height_cm,
        camera_offset_y_cm
    )

    app.set_head_position((0, -camera_offset_y_cm, 60))
    
    def update_view(task):
        with result_lock:
            result = latest_result

        if result is not None:
            position, face_found, timestamp = result

            if face_found and position is not None:
                app.set_head_position(position)

        return task.cont

    app.taskMgr.add(update_view, "receive_tracking", sort=-10)

    tracking_thread = threading.Thread(
        target=eye_tracking,
        args=(config,),
        daemon=True
    )

    tracking_thread.start()
    app.accept("escape", app.userExit)

    try:
        app.run()

    finally:
        stop_tracking.set()
        tracking_thread.join(timeout=5)
        app.destroy()

main()
