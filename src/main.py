import threading
import time
import random


class EyeTrackingResult:
    def __init__(self, left_x, left_y, right_x, right_y):
        self.left_x = left_x
        self.left_y = left_y
        self.right_x = right_x
        self.right_y = right_y


result_lock = threading.Lock()
current_eye_tracing_result = None


def eye_tracking():
    while True:
        global current_eye_tracing_result

        # Simulate values for now
        result = EyeTrackingResult(
            left_x=random.random(),
            left_y=random.random(),
            right_x=random.random(),
            right_y=random.random(),
        )

        with result_lock:
            current_eye_tracing_result = result

        # Simulate 30 FPS
        time.sleep(0.0333)


def rendering():
    while True:
        result_lock.acquire()
        result_copy = current_eye_tracing_result
        result_lock.release()

        # All rendering and parallax calculations here
        if result_copy is not None:
            print(f"Rendering coordinates "
                  f"{result_copy.left_x},"
                  f"{result_copy.left_y}, "
                  f"{result_copy.right_x}, "
                  f"{result_copy.right_y}"
                  )
        else:
            print(f"Result none")

        # Simulate 60 Hz
        time.sleep(0.0166)


t_eye_tracking = threading.Thread(target=eye_tracking)
t_rendering = threading.Thread(target=rendering)

t_eye_tracking.start()
t_rendering.start()
