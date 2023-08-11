import cv2
import numpy as np
from object_detector import *

# Load Aruco detector
parameters = cv2.aruco.DetectorParameters_create()
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)

# Load Object Detector
detector = HomogeneousBgDetector()

# Load Camera Footage
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#Image Loading (if using a single image)
#img = cv2.imread("phone_aruco_marker.jpg")   #define image to analyse

class Marker:
    def __init__(self, x, y, ID):
        self.x = x
        self.y = y
        self.ID = ID
        self.role = self.assign_role()

    def assign_role(self):
        if self.ID == 1:
            return "TL"
        elif self.ID == 2:
            return "TR"
        elif self.ID == 3:
            return "BR"
        elif self.ID == 4:
            return "BL"
        else:
            return "Unknown"

    def __repr__(self):
        return f"Marker(ID: {self.ID}, Position: ({self.x}, {self.y}), Role: {self.role})"


def read_markers():
    marker_list = []
    
    while True:
        _, img = cap.read()

        # Detect Aruco markers
        corners, ids, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)

        if ids is not None:
            for i, corner in enumerate(corners):
                int_corner = np.int32(corner)
                
                # Draw green polygon around the marker
                cv2.polylines(img, [int_corner], True, (0, 255, 0), 5)
                
                # Calculate the center of the marker
                center = tuple(np.mean(int_corner[0], axis=0).astype(int))

                marker = Marker(center[0], center[1], ids[i][0])
                marker_list.append(marker)

                # Draw red circle at the center
                cv2.circle(img, center, 5, (0, 0, 255), -1)
                
                # Display the marker ID
                cv2.putText(img, "ID: " + str(ids[i][0]), (center[0] - 20, center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                

        cv2.imshow("Image", img)
        key = cv2.waitKey(10000)  # take a new picture every 10 000ms
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return marker_list

if __name__ == "__main__":
    marker_data = read_markers()

    for marker in marker_data:
        print(marker)
        print(marker.ID)
        print(marker.x)
    
