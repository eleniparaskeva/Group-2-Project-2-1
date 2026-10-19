import json
import threading
import time
from eyetracker import EyeTracker


class EyeTrackingResult:
    def __init__(self, x, y, z, face_found, timestamp):
        self.x = x
        self.y = y
        self.z = z
        self.face_found = face_found
        self.timestamp = timestamp


result_lock = threading.Lock()
current_eye_tracing_result = None


def eye_tracking():

    with open("config.json") as f:
        config = json.load(f)

    eyetracker = EyeTracker(config)

    while eyetracker.update():
        global current_eye_tracing_result

        if eyetracker.get_position() is None:
            continue
        position, face_found, timestamp = eyetracker.get_result()
        x, y, z = position
        result = EyeTrackingResult(x, y, z, face_found, timestamp)

        with result_lock:
            current_eye_tracing_result = result


def rendering():
    while True:
        result_lock.acquire()
        result_copy = current_eye_tracing_result
        result_lock.release()

        # All rendering and parallax calculations here
        if result_copy is not None:
            print(f"Rendering coordinates "
                  f"{result_copy.x},"
                  f"{result_copy.y}, "
                  f"{result_copy.z}"
                  )
        else:
            print(f"Result none")

        # Simulate 60 Hz
        time.sleep(1)


t_eye_tracking = threading.Thread(target=eye_tracking)
t_rendering = threading.Thread(target=rendering)

t_eye_tracking.start()
t_rendering.start()
