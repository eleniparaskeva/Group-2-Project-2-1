import os
import time
import csv
import json
import urllib.request
from collections import deque
from unittest import result

import cv2
import mediapipe
import numpy
from mediapipe.tasks import python as mediapipe_python
from mediapipe.tasks.python import vision

with open("config.json") as f:
    config = json.load(f)

CAMERA_INDEX = config["camera_index"]
FRAME_WIDTH = config["frame_width"]
FRAME_HEIGHT = config["frame_height"]
MODEL_PATH = config["model_path"]
MODEL_URL = config["model_url"]

# numbers of mediapipe landmarks
LEFT_IRIS = 468
RIGHT_IRIS = 473

WINDOW_FRAMERATE = 30 # used for fps and jitter

def download_model_if_missing():
    if os.path.exists(MODEL_PATH):
        return
    print("Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded")

def create_landmarker():
    base_options = mediapipe_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(options=options)

def calculate_jitter(positions):
# positions is a list of (x,y) tuples
    if len(positions) < 2:
        return 0.0, 0.0 # no jitter between 0 or 1 positions
    positions_array = numpy.array(positions)
    jitter_x = positions_array[:, 0].std()
    jitter_y = positions_array[:, 1].std()
    return jitter_x, jitter_y

def print_summary(fps_list, latency_list, frames, lost, duration):
    print("\n===== Recording finished =====")
    print("Duration: %.1f s" % duration)
    print("Total frames: %d, lost: %d (%.1f %%)" % (frames, lost, 100.0 * lost / max(frames, 1)))
    if len(fps_list) > 0:
        print("FPS: mean %.1f" % numpy.mean(fps_list))
        print("Latency: mean %.1f ms, max %.1f ms" % (numpy.mean(latency_list), numpy.max(latency_list)))

def main():

    download_model_if_missing()
    landmarker = create_landmarker()

    capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    if not capture.isOpened():
        print("Could not open camera.")
        return

    frame_times = deque(maxlen=WINDOW_FRAMERATE)
    positions = deque(maxlen=WINDOW_FRAMERATE)
    jitter_x, jitter_y = 0.0, 0.0
    fps = 0.0

    recording = False
    csv_file = None # gets created when recording starts
    writer = None
    rec_start = 0.0 # get reset for every new recording
    rec_total_frames = 0
    rec_lost_frames = 0
    rec_fps_list = []
    rec_latency_list = []

    last_timestamp = -1 # in ms
    start_time = time.time()

    print("r = start recording, s = stop recording, q = quit")

    # main loop:
    while True:
        ok, frame = capture.read()
        capture_time = time.time()
        if not ok:
            print("Could not read frame.")
            break
        height_pixels = frame.shape[0]
        width_pixels = frame.shape[1]

        frame_times.append(capture_time)
        if len(frame_times) >= 2: # at least two frames for time difference
            amount_intervals = len(frame_times) - 1 # for N frames there are N - 1 intervals between frames
            time_interval = frame_times[-1] - frame_times[0] # index -1 = newest frame (end of list), index 0 = oldest frame
            fps = amount_intervals / time_interval

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_format = mediapipe.ImageFormat.SRGB
        mediapipe_image = mediapipe.Image(image_format = image_format, data = rgb)

        timestamp_ms = int((capture_time - start_time) * 1000)
        if timestamp_ms <= last_timestamp:
            timestamp_ms = last_timestamp + 1
        last_timestamp = timestamp_ms

        result = landmarker.detect_for_video(mediapipe_image, timestamp_ms)
        latency_ms = (time.time() - capture_time) * 1000.0 # includes color conversion, mediapipe

        face_found = len(result.face_landmarks) > 0
        mid_x, mid_y = "", "" # empty in csv if no face

        if face_found:
            landmarks = result.face_landmarks[0]
            lx, ly = landmarks[LEFT_IRIS].x * width_pixels, landmarks[LEFT_IRIS].y * height_pixels
            rx, ry = landmarks[RIGHT_IRIS].x * width_pixels, landmarks[RIGHT_IRIS].y * height_pixels
            mid_x = (lx + rx) / 2
            mid_y = (ly + ry) / 2

            positions.append((mid_x, mid_y))
            jitter_x, jitter_y = calculate_jitter(positions)

            cv2.circle(frame, (int(mid_x), int(mid_y)), 5, (0, 0, 255), 2)
            cv2.circle(frame, (int(rx), int(ry)), 5, (255, 0, 0), 2)
            cv2.circle(frame, (int(lx), int(ly)), 5, (255, 0, 0), 2)

        cv2.putText(frame, "FPS: %.1f latency: %.1f ms" % (fps, latency_ms), (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, "jitter x %.2f y %.2f px" % (jitter_x, jitter_y), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, "frames total: %d lost: %d " % (rec_total_frames, rec_lost_frames), (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if not face_found:
            cv2.putText(frame, "NO FACE", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        if recording:
            cv2.circle(frame, (width_pixels -25, 25), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (width_pixels - 80, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Press r to record", (width_pixels - 120, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("MediaPipe Test", frame)

        if recording:
            rec_total_frames += 1
            if not face_found:
                rec_lost_frames += 1
            rec_fps_list.append(fps)
            rec_latency_list.append(latency_ms)

            writer.writerow([
                round(time.time() - rec_start, 4),
                round(fps, 2),
                round(latency_ms, 2),
                1 if face_found else 0,
                rec_total_frames,
                rec_lost_frames,
                round(jitter_x, 3),
                round(jitter_y, 3),
                mid_x,
                mid_y,
            ])
            csv_file.flush()

        key = cv2.waitKey(1) & 0xFF

        if key == ord("r") and not recording:
            filename = "recording_" + time.strftime("%Y%m%d_%H%M%S") + ".csv"
            csv_file = open(filename, "w", newline="")
            writer = csv.writer(csv_file)
            writer.writerow(["time_s", "fps", "latency_ms", "face_found", "total_frames", "lost_frames", "jitter_x", "jitter_y", "mid_x", "mid_y"])
            rec_start = time.time()
            rec_total_frames = 0
            rec_lost_frames = 0
            rec_fps_list = []
            rec_latency_list = []
            recording = True
            print("Recording started. Writing to data to " + filename)

        elif key == ord("s") and recording:
            recording = False
            csv_file.close()
            print_summary(rec_fps_list, rec_latency_list, rec_total_frames, rec_lost_frames, time.time() - rec_start)

        elif key == ord("q"):
            break

    if recording:
        csv_file.close()
        print_summary(rec_fps_list, rec_latency_list, rec_total_frames, rec_lost_frames, time.time() - rec_start)

    capture.release()
    cv2.destroyAllWindows()
    landmarker.close()


if __name__ == "__main__":
    main()