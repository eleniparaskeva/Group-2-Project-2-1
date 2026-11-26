import json
import cv2
import numpy as np
from panda3d.core import Texture, TextNode
from direct.gui.OnscreenImage import OnscreenImage
from screens.screen import Screen
from view import style

# copied from calibrate_checkerboard.py
BOARD_COLS = 8
BOARD_ROWS = 6
PATTERN_SIZE = (BOARD_COLS, BOARD_ROWS)
MIN_VIEWS = 10


def calibrate(object_points, image_points, image_size):
    print('starting calibration...')
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(object_points, image_points, image_size, None,None)

    fx = camera_matrix[0][0]
    fy = camera_matrix[1][1]

    total_error = 0
    for i in range(len(object_points)):
        projected, _ = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
        error = cv2.norm(image_points[i].reshape(-1, 2), projected.reshape(-1, 2), cv2.NORM_L2) / len(projected)
        total_error = total_error + error
    mean_error = total_error / len(object_points)

    focal = (fx + fy) / 2
    print('fx = %.1f, fy = %.1f, mean reprojection error = %.3f px' % (fx, fy, mean_error))
    return focal, mean_error


class CalibrateScreen(Screen):

    def __init__(self, app):
        super().__init__(app)

        board_points = []
        for x in range(BOARD_ROWS):
            for y in range(BOARD_COLS):
                board_points.append([y, x, 0])
        self.board_points = np.array(board_points, np.float32)

        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        self.capture = None
        self.object_points = []
        self.image_points = []
        self.image_size = None
        self.found = False
        self.corners = None
        self.result = None

        # webcam frames get copied into this texture every frame
        self.texture = Texture("webcam")
        self.texture_size = None

        left = -app.getAspectRatio()
        style.make_label(self.root, "CALIBRATE - CHECKERBOARD", (left + 0.08, 0.88))

        box = style.pixel_box(self.root, -0.68, 0.68, -0.5, 0.54)
        self.image = OnscreenImage(image=self.texture, parent=box, pos=(0, 0, 0.02), scale=(0.64, 1, 0.48))

        self.status = style.make_text(self.root, "", (-0.68, -0.61))
        self.result_text = style.make_value(self.root, "", (-0.68, -0.71))
        self.message = style.make_text(self.root, "", (-0.68, -0.81))
        style.make_text(self.root, "[SPACE] capture    [C] calibrate    [S] save    [ESC] back", (0, -0.93), scale=0.06, align=TextNode.ACenter)

    def show(self):
        super().show()
        self.app.setBackgroundColor(style.to_linear(style.BLUE))
        self.app.grid.show()

        config = self.app.app_config
        self.capture = cv2.VideoCapture(config['camera_index'], cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config['frame_width'])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config['frame_height'])

        self.object_points = []
        self.image_points = []
        self.result = None
        self.result_text.hide()
        self.message.setText("")

        if not self.capture.isOpened():
            self.status.setText("cannot open camera")
        else:
            self.app.taskMgr.add(self.update_camera, "calibration_camera")

        self.accept("space", self.capture_view)
        self.accept("c", self.run_calibration)
        self.accept("s", self.save_result)
        self.accept("escape", self.app.switch_to, ["menu"])

    def hide(self):
        super().hide()
        self.app.grid.hide()
        self.app.taskMgr.remove("calibration_camera")

        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def update_camera(self, task):
        ok, frame = self.capture.read()
        if not ok:
            self.status.setText("cannot read frame")
            return task.cont

        height, width = frame.shape[:2]
        self.image_size = (width, height)

        display = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
        found, corners = cv2.findChessboardCorners(gray, PATTERN_SIZE, None, flags)

        if found:
            corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), self.criteria)
            cv2.drawChessboardCorners(display, PATTERN_SIZE, corners, found)
            if len(self.image_points) < MIN_VIEWS:
                self.status.setText('%d / %d views, press SPACE to capture' % (len(self.image_points), MIN_VIEWS))
            else:
                self.status.setText('%d views, press SPACE to capture more or C to calibrate' % len(self.image_points))
        else:
            self.status.setText('board not found (%d / %d views)' % (len(self.image_points), MIN_VIEWS))

        self.found = found
        self.corners = corners
        self.show_frame(display)
        return task.cont

    def show_frame(self, frame):
        height, width = frame.shape[:2]
        if self.texture_size != (width, height):
            self.texture.setup2dTexture(width, height, Texture.T_unsigned_byte, Texture.F_rgb)
            self.texture_size = (width, height)

        # panda textures start at the bottom left, opencv images at the top left
        frame = cv2.flip(frame, 0)
        self.texture.setRamImageAs(frame.tobytes(), "BGR")

    def capture_view(self):
        if self.found:
            self.object_points.append(self.board_points)
            self.image_points.append(self.corners)
            self.message.setText('saved view no. %d' % len(self.image_points))
        else:
            self.message.setText('board not found, view not saved')

    def run_calibration(self):
        if len(self.image_points) < MIN_VIEWS:
            self.message.setText('not enough views for calibration')
            return

        self.result, error = calibrate(self.object_points, self.image_points, self.image_size)
        self.result_text.setText('focal_px = %.1f  (error %.2f px, old %.1f)' % (self.result, error, self.app.app_config["focal_px"]))
        self.result_text.show()
        self.message.setText('press S to save or capture new views to restart')
        self.object_points = []
        self.image_points = []

    def save_result(self):
        if self.result is None:
            self.message.setText('no calibration done yet')
            return

        with open("../config.json") as f:
            config = json.load(f)
        config["focal_px"] = round(self.result, 1)
        with open("../config.json", "w") as f:
            json.dump(config, f, indent=4)

        # so launch uses the new value without restarting
        self.app.app_config["focal_px"] = round(self.result, 1)
        self.message.setText("saved focal_px = %.1f to config.json" % self.result)
