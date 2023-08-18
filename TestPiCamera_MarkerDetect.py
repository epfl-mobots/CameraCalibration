import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
from object_detector import *

# Load Aruco detector
parameters = cv2.aruco.DetectorParameters_create()
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)

# Load Object Detector
detector = HomogeneousBgDetector()

# Setup the Raspberry Pi camera
camera = PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 30
raw_capture = PiRGBArray(camera, size=(1280, 720))

def read_markers():
    marker_list = []

    for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
        img = frame.array

        # Detect Aruco markers
        corners, ids, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)

        if ids is not None:
            for i, corner in enumerate(corners):
                int_corner = np.int32(corner)
                
                # Draw green polygon around the marker
                cv2.polylines(img, [int_corner], True, (0, 255, 0), 5)

                # Calculate the center of the marker
                center = tuple(np.mean(int_corner[0], axis=0).astype(int))
                
                # Draw red circle at the center
                cv2.circle(img, center, 5, (0, 0, 255), -1)
                
                # Display the marker ID
                cv2.putText(img, "ID: " + str(ids[i][0]), (center[0] - 20, center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Store center and ID in the list
                marker_list.append((center, ids[i][0]))

        cv2.imshow("Image", img)
        raw_capture.truncate(0)  # clear the stream for the next frame

        key = cv2.waitKey(1)
        if key == 27:
            break

    cv2.destroyAllWindows()
    return marker_list

if __name__ == "__main__":
    marker_data = read_markers()

    # Print center coordinates of markers and their IDs
    for (x, y), marker_id in marker_data:
        print(f"Marker ID: {marker_id}, Center: ({x}, {y})")
