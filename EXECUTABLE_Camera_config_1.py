import cv2
import numpy as np
import keyboard
import time
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
    
    # Check if the camera is properly opened
    if not cap.isOpened():
        print("Error: Camera not initialized properly.")
        return []

    ret, img = cap.read()

    # Check if the frame is valid
    if not ret or img is None:
        print("Error: Failed to read frame from camera.")
        return []

    marker_list = []

    # Detect Aruco markers
    corners, ids, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)
    print("WentThroughDetection")

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
    key = cv2.waitKey(1000)
    if key == 27:
        cap.release()
        cv2.destroyAllWindows()

    return marker_list


def set_camera(marker_list):

    n = 4  # Expected number of markers
    wait_t = 5  # Waiting time in seconds
    count = 0

    # Make sure all markers are visible, else move back. Assuming the camera is roughly aligned before starting this program.
    while len(marker_list) != n:        
        count = count + 1
        print(f"Count #: {count}")

        if len(marker_list) > n:
            print("Error in marker recognition. Too many were recognized. Make sure the camera has proper visibility.")
        else:
            print("Make sure all (4) markers are visible by the camera. Not enough were recognized.")
        
        time.sleep(wait_t)
        print("Let's see if they are all visible now.")
        marker_list = read_markers()  # Update the marker list but there's an error
        test_n_markers = False
        
        if count >= 10:
            print("Too many errors counting markers.")
            break
        
    test_n_markers = True
        
    for marker in marker_list:
        print(marker)
        print(marker.ID)
        print(marker.x)

    if (test_n_markers == True):
        success_ = True
        return success_
    if (test_n_markers == False):
        success_ = False
        return success_

def intro_soft():

    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")
    print("To continue, press 'C' on the keyboard (key #67).")
  
    while True:
        event = keyboard.read_event()
        
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'c':
                 return
   

if __name__ == "__main__":
    intro_soft()
    marker_list = read_markers()
    success = set_camera(marker_list)
    
