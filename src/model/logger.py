import os
import csv
import json
import time
import numpy

TRACKING_HEADER = ["time_s", "face_found", "camera_read_ms", "preprocess_ms", "landmarker_detection_ms",
                   "position_calculation_ms", "smoothing_ms", "total_ms", "raw_x", "raw_y",
                   "z_hvid", "z_ipd", "smooth_x", "smooth_y", "smooth_z", "smoothing"]
RENDER_HEADER = ["time_s", "frame_ms", "data_age_ms", "face_found"]

# render frames slower than this count as slow (below 60 fps)
SLOW_FRAME_MS = 1000 / 60


def load_experiment_config():
    with open("../../experiment_config.json") as f:
        experiment_config = json.load(f)
        return experiment_config


class Logger:
    def __init__(self, config, experiment_config):
        self.config = config
        self.experiment_config = experiment_config
        self.name = experiment_config["experiment"]
        self.duration_s = experiment_config["duration_s"]
        self.warmup_s = experiment_config["warmup_s"]
        self.folder = experiment_config["folder"]
        self.notes = experiment_config["notes"]
        self.tracking_rows = []
        self.render_rows = []

        self.start_time = time.monotonic()
        print("Logger started: " + self.name)

    def get_time(self):
        # time since the measurement started (negative during warm-up)
        return time.monotonic() - self.start_time - self.warmup_s

    def is_measuring(self):
        t = self.get_time()
        return t >= 0 and t < self.duration_s

    def is_done(self):
        return self.get_time() >= self.duration_s

    def add_tracking_row(self, face_found, times, raw, z_hvid, z_ipd, smoothed, smoothing_name):
        # camera_read is NOT in total
        total_ms = times["preprocess"] + times["landmarker_detection"] + times["position_calculation"] + times["smoothing"]

        row = [round(self.get_time(), 4), int(face_found), times["camera_read"], times["preprocess"],
               times["landmarker_detection"], times["position_calculation"], times["smoothing"], total_ms]

        if face_found:
            row = row + [raw[0], raw[1], z_hvid, z_ipd, smoothed[0], smoothed[1], smoothed[2]]
        else:
            row = row + ["", "", "", "", "", "", ""]  # empty row if no face

        row.append(smoothing_name)
        self.tracking_rows.append(row)

    def add_render_row(self, frame_ms, data_age_ms, face_found):
        row = [round(self.get_time(), 4), frame_ms, data_age_ms, int(face_found)]
        self.render_rows.append(row)

    def find_run_number(self):
        run = 1
        while os.path.exists(os.path.join(self.folder, self.name + "_run" + str(run) + "_tracking.csv")):
            run = run + 1
        return run

    def write_csv(self, filename, header, rows):
        with open(os.path.join(self.folder, filename), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)

    def save(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        run = self.find_run_number()
        tracking_file = self.name + "_run" + str(run) + "_tracking.csv"
        render_file = self.name + "_run" + str(run) + "_render.csv"

        self.write_csv(tracking_file, TRACKING_HEADER, self.tracking_rows)
        self.write_csv(render_file, RENDER_HEADER, self.render_rows)

        lost = 0
        total_times = []
        raw_x = []
        raw_y = []
        raw_z = []
        z_col = TRACKING_HEADER.index("z_hvid")  # z_hvid is the raw z now

        for row in self.tracking_rows:
            total_times.append(row[7])
            if row[1] == 1:
                raw_x.append(row[8])
                raw_y.append(row[9])
                raw_z.append(row[z_col])
            else:
                lost = lost + 1

        frame_times = []
        for row in self.render_rows:
            frame_times.append(row[1])

        slow = 0
        for frame_ms in frame_times:
            if frame_ms > SLOW_FRAME_MS:
                slow = slow + 1

        smoothing_name = ""
        if len(self.tracking_rows) > 0:
            smoothing_name = self.tracking_rows[-1][15]

        # write the entry for experiments_log.md
        text = "## " + self.name + " run " + str(run) + " (" + time.strftime("%Y-%m-%d %H:%M") + ")\n"
        if self.notes != "":
            text += "Notes: " + self.notes + "\n"
        text += "\n"
        text += "- Duration: %s s (+%s s warm-up), smoothing: %s\n" % (self.duration_s, self.warmup_s, smoothing_name)
        text += "- Files: " + tracking_file + ", " + render_file + "\n"

        if len(self.tracking_rows) > 0:
            frames = len(self.tracking_rows)
            text += "- Tracking: %d frames, %.1f %% lost, %.1f Hz\n" % (frames, 100 * lost / frames, frames / self.duration_s)
            text += "- Tracking latency: median %.1f ms, P95 %.1f ms\n" % (numpy.median(total_times), numpy.percentile(total_times, 95))

        if len(frame_times) > 0:
            text += "- Rendering: mean %.1f FPS, P95 frame time %.1f ms, %.1f %% frames > 16.7 ms\n" % (
                len(frame_times) / self.duration_s, numpy.percentile(frame_times, 95), 100 * slow / len(frame_times))

        if len(raw_x) > 1:
            text += "- Jitter (raw, SD): x %.2f cm, y %.2f cm, z %.2f cm\n" % (numpy.std(raw_x), numpy.std(raw_y), numpy.std(raw_z))

        text += "\nexperiment_config.json:\n```json\n" + json.dumps(self.experiment_config, indent=4) + "\n```\n"
        text += "config.json:\n```json\n" + json.dumps(self.config, indent=4) + "\n```\n\n"

        with open(os.path.join(self.folder, "experiments_log.md"), "a") as f:
            f.write(text)

        print("Saved " + self.name + " run " + str(run))
