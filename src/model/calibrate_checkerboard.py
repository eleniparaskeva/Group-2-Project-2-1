import json
import cv2
import numpy as np
from eyetracker import open_config

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
    return focal

def main():
    config = open_config()

    capture = cv2.VideoCapture(config['camera_index'], cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config['frame_width'])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config['frame_height'])

    if not capture.isOpened():
        print('cannot open camera')
        return

    board_points = []
    for x in range(BOARD_ROWS):
        for y in range(BOARD_COLS):
            board_points.append([y, x, 0])
    board_points = np.array(board_points, np.float32)

    object_points = []
    image_points = []

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    result = None

    while True:
        ok, frame = capture.read()
        if not ok:
            print('cannot read frame')
            break

        height, width = frame.shape[:2]
        image_size = (width, height)

        display = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
        found, corners = cv2.findChessboardCorners(gray, PATTERN_SIZE, None, flags)

        if found:
            corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            cv2.drawChessboardCorners(display, PATTERN_SIZE, corners, found)
            if len(image_points) < MIN_VIEWS:
                status = '%d / %d views, press SPACE to capture or q to quit' % (len(image_points), MIN_VIEWS)
            else:
                status = '%d views, press SPACE to capture more or c to calibrate focal length' % len(image_points)
            cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            if result is not None:
                cv2.putText(display, 'last result: focal_px = %.1f' % result, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            cv2.putText(display, 'board not found', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('calibration', display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord(' '):
            if found:
                object_points.append(board_points)
                image_points.append(corners)
                print('saved view no. %d' % len(image_points))
            else:
                print('board not found, view not saved')
        elif key == ord('c'):
            if len(image_points) < MIN_VIEWS:
                print('not enough views for calibration')
            else:
                result = calibrate(object_points, image_points, image_size)
                print('calibration result: %.1f' % result)
                print('press s to save or capture new view to restart')
                object_points = []
                image_points = []
        elif key == ord('s'):
            if result is None:
                print('no calibration done yet')
            else:
                with open("../config.json") as f:
                    config = json.load(f)
                config["focal_px"] = round(result, 1)
                with open("../config.json", "w") as f:
                    json.dump(config, f, indent=4)
                print("saved focal_px = %.1f to config.json" % result)

    capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()