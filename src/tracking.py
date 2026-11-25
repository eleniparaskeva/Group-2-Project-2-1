import threading
from queue import SimpleQueue, Empty
from model.eyetracker import EyeTracker


class TrackingService:

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

        self.lock = threading.Lock()
        self.latest_result = None
        self.stop_event = threading.Event()
        self.commands = SimpleQueue()
        self.thread = None

    def start(self):
        if self.is_running():
            return

        self.stop_event.clear()
        with self.lock:
            self.latest_result = None

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.thread is None:
            return

        self.stop_event.set()
        self.thread.join(timeout=5)
        self.thread = None

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def set_logger(self, logger):
        self.logger = logger

    def cycle_smoothing(self):
        self.commands.put("cycle")

    def get_result(self):
        # (position, face_found, timestamp, smoothing_name) or None
        with self.lock:
            return self.latest_result

    def handle_commands(self, tracker):
        while True:
            try:
                command = self.commands.get_nowait()
            except Empty:
                break

            if command == "cycle":
                tracker.smoothing.cycle()

    def run(self):
        tracker = None

        try:
            tracker = EyeTracker(self.config)

            while not self.stop_event.is_set():
                self.handle_commands(tracker)

                if not tracker.update():
                    break

                logger = self.logger
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

                if self.config["show_visualization"]:
                    tracker.visualize()

                result = (*tracker.get_result(), tracker.smoothing.name)

                with self.lock:
                    self.latest_result = result

        except Exception as error:
            print("Eye tracking error:", error)

        finally:
            if tracker is not None:
                tracker.close()
