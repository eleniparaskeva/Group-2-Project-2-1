import math
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
        self.position = None
        self.timestamp = None
        self.ipd_cm = config["ipd_cm"]
        self.focal_px = config["focal_px"]
        self.alpha = config["smoothing_alpha"]

    def compute_position(self):
        if self.face_found:
            old_position = self.position

            d_px = math.hypot(self.points['left_center'][0] - self.points['right_center'][0], self.points['right_center'][1] - self.points['left_center'][1])
            z = self.focal_px * self.ipd_cm / d_px

            (mx, my) = ((self.points['left_center'][0] + self.points['right_center'][0]) / 2, (self.points['left_center'][1] + self.points['right_center'][1]) / 2)

            height, width = self.frame.shape[:2]
            (cx, cy) = (width / 2, height / 2)

            x = -(mx - cx) * z / self.focal_px
            y = -(my - cy) * z / self.focal_px


            if old_position is not None:
                x = self.alpha * x + (1 - self.alpha) * old_position[0]
                y = self.alpha * y + (1 - self.alpha) * old_position[1]
                z = self.alpha * z + (1 - self.alpha) * old_position[2]

            self.position = (x, y, z) # +x = right, +y = up, +z = forward

    def close(self):
        self.capture.release()
        self.landmarker.close()
        print('Tracker closed')


    def update(self):
        ok, self.frame = self.capture.read()
        self.timestamp = int(time.monotonic() * 1000)

        if not ok:
            print("Could not read frame.")
            return False

        height, width = self.frame.shape[:2]

        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        image_format = mediapipe.ImageFormat.SRGB
        mediapipe_image = mediapipe.Image(image_format=image_format, data=rgb)

        result = (self.landmarker.detect_for_video(mediapipe_image, self.timestamp))
        self.face_found = len(result.face_landmarks) > 0

        if self.face_found:
            # print("Face found")
            face = result.face_landmarks[0]
            for name, index in LANDMARKS.items():
                self.points[name] = landmark_to_px(face[index], width, height)
            self.compute_position()

        return True

    def get_position(self):
        return self.position

    def get_result(self):
        return self.position, self.face_found, self.timestamp

    def visualize(self):
        if self.frame is None:
            return False

        image = cv2.flip(self.frame, 1)
        height, width = image.shape[:2]

        origin = (int(width / 2), int(height / 2))
        white = (255, 255, 255)
        gray = (140, 140, 140)
        spacing = 80

        for x in range(0, width + 1, spacing):
            cv2.line(image, origin, (x, 0), gray, 1)
            cv2.line(image, origin, (x, height), gray, 1)
        for y in range(0, height + 1, spacing):
            cv2.line(image, origin, (0, y), gray, 1)
            cv2.line(image, origin, (width, y), gray, 1)

        for k in range(1, 10):
            half_w = int(width / 2 / k)
            half_h = int(height / 2 / k)
            cv2.rectangle(image, (origin[0] - half_w, origin[1] - half_h), (origin[0] + half_w, origin[1] + half_h), gray, 1)

        cv2.arrowedLine(image, (0, origin[1]), (width, origin[1]), white, 1, tipLength=0.03)
        cv2.arrowedLine(image, (origin[0], height), (origin[0], 0), white, 1, tipLength=0.03)
        cv2.circle(image, origin, 2, white, -1)

        if self.face_found:
            left = (width - self.points["left_center"][0], self.points["left_center"][1])
            right = (width - self.points["right_center"][0], self.points["right_center"][1])
            cv2.circle(image, (int(left[0]), int(left[1])), 3, (168, 124, 234), -1)
            cv2.circle(image, (int(right[0]), int(right[1])), 3, (170, 234, 86), -1)

            middle = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
            cv2.circle(image, (int(middle[0]), int(middle[1])), 5, (159, 252, 246), -1)

            cv2.putText(image, "face found", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            cv2.putText(image, "no face", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        scale = 0.6
        image = cv2.resize(image, (int(width * scale), int(height * scale)))

        cv2.imshow("webcam", image)
        if cv2.waitKey(1) == ord('q'):
            return False
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
            x, y, z = tracker.position
            text = "x=%.1f  y=%.1f  z=%.1f cm" % (x, y, z)
            cv2.putText(tracker.frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("tracker", tracker.frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()