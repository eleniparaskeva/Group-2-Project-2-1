import os
import time
import json
import urllib.request
import cv2
import mediapipe
from mediapipe.tasks import python as mediapipe_python
from mediapipe.tasks.python import vision

LANDMARKS = {"left_center": 468, "left_inner": 469, "left_outer": 471, "right_center": 473, "right_inner": 476, "right_outer": 474}

def open_config():
    with open("config.json") as f:
        config = json.load(f)
        return config

def download_model_if_missing(model_path, model_url):
    if os.path.exists(model_path):
        return
    print("Downloading model...")
    urllib.request.urlretrieve(model_url, model_path)
    print("Model downloaded")

def create_landmarker(model_path):
    base_options = mediapipe_python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(options=options)

def landmark_to_px(NormalizedLandmark, width, height):
    x = NormalizedLandmark.x * width
    y = NormalizedLandmark.y * height
    return x, y

def draw_point(frame, point, color):
    cv2.circle(frame, (int(point[0]), int(point[1])), 1, color, -1)


class EyeTracker:
    def __init__(self, config):
        download_model_if_missing(config["model_path"], config["model_url"])
        self.landmarker = create_landmarker(config["model_path"])
        print('Tracker created')

        self.capture = cv2.VideoCapture(config["camera_index"], cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config["frame_width"])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config["frame_height"])

        if not self.capture.isOpened():
            raise RuntimeError("Could not open camera " + str(config["camera_index"]))

        self.face_found = False
        self.points = {}
        self.frame = None

    def close(self):
        self.capture.release()
        self.landmarker.close()
        print('Tracker closed')


    def update(self):
        ok, self.frame = self.capture.read()
        timestamp = int(time.monotonic() * 1000)

        if not ok:
            print("Could not read frame.")
            return False

        height, width = self.frame.shape[:2]

        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        image_format = mediapipe.ImageFormat.SRGB
        mediapipe_image = mediapipe.Image(image_format=image_format, data=rgb)

        result = (self.landmarker.detect_for_video(mediapipe_image, timestamp))
        self.face_found = len(result.face_landmarks) > 0

        if self.face_found:
            # print("Face found")
            face = result.face_landmarks[0]
            for name, index in LANDMARKS.items():
                self.points[name] = landmark_to_px(face[index], width, height)

        return True


def main():

    config = open_config()
    tracker = EyeTracker(config)
    while(tracker.update()):

        if tracker.face_found:
            for name, point in tracker.points.items():
                if name.startswith("left"):
                    color = (168, 124, 234)
                else:
                    color = (170, 234, 86)
                draw_point(tracker.frame, point, color)

        cv2.imshow("tracker", tracker.frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    tracker.close()
    cv2.destroyAllWindows()


'''
    download_model_if_missing()
    landmarker = create_landmarker()

    capture = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    while True:
        ok, frame = capture.read()
        timestamp = int(time.monotonic() * 1000)

        if not ok:
            print("Could not read frame.")
            break

        height, width = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_format = mediapipe.ImageFormat.SRGB
        mediapipe_image = mediapipe.Image(image_format=image_format, data=rgb)

        result = landmarker.detect_for_video(mediapipe_image, timestamp)
        face_found = len(result.face_landmarks) > 0


        if face_found:
            #print("Face found")
            face = result.face_landmarks[0]

            left_center = landmark_to_px(face[LEFT_CENTER], width, height)
            left_inner = landmark_to_px(face[LEFT_INNER], width, height)
            left_outer = landmark_to_px(face[LEFT_OUTER], width, height)
            right_center = landmark_to_px(face[RIGHT_CENTER], width, height)
            right_inner = landmark_to_px(face[RIGHT_INNER], width, height)
            right_outer = landmark_to_px(face[RIGHT_OUTER], width, height)

            print(left_center, left_inner, left_outer, right_center, right_inner, right_outer)

            draw_landmark(frame, left_center[0], left_center[1], 168, 124, 234)
            draw_landmark(frame, left_inner[0], left_inner[1], 168, 124, 234)
            draw_landmark(frame, left_outer[0], left_outer[1], 168, 124, 234)
            draw_landmark(frame, right_center[0], right_center[1], 170, 234, 86)
            draw_landmark(frame, right_inner[0], right_inner[1], 170, 234, 86)
            draw_landmark(frame, right_outer[0], right_outer[1], 170, 234, 86)

            cv2.imshow('Eyetracking', frame)

        else:
            print("Face not found")


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()
'''

if __name__ == "__main__":
    main()