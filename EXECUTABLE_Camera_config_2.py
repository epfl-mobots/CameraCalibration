import cv2
import numpy as np
import keyboard
import time
import math
import sys
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


def countIsValid(marker_list):

    n = 4  # Expected number of markers
    wait_t = 3  # Waiting time in seconds

    if len(marker_list) == n:
        print("Valid marker count.")
        return True

    elif len(marker_list) == 0:
        print("Let's do our first marker reading.")
    elif len(marker_list) < n:
        print("Make sure all (4) markers are visible by the camera. Not enough were recognized.")
    else:
        print("Error in marker recognition. Too many were recognized. Make sure the camera has proper visibility.")

    time.sleep(wait_t)
    print("Let's see if they are all visible now.")
    time.sleep(0.5*wait_t)

    return False


def intro_soft():

    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")
    print("To continue, press 'C' on the keyboard (key #67).")
  
    while True:
        event = keyboard.read_event()
        
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'c':
                 return

def NewAcquisition():

    count = 0

    marker_list = read_markers()

    while not countIsValid(marker_list):
        count = count + 1
        if count >= 5:
            print("Too many errors counting markers.")
            sys.exit(1)
        else:
            marker_list = read_markers()

    return marker_list

def Rx_Feedback(marker_list):

    X_BL = 0
    X_BR = 0
    X_TL = 0
    X_TR = 0

    Y_BL = 0
    Y_BR = 0
    Y_TL = 0
    Y_TR = 0
 
    for marker in marker_list:
        if marker.role == "BL":
            X_BL = marker.x
            Y_BL = marker.y
        elif marker.role == "BR":
            X_BR = marker.x
            Y_BR = marker.y
        elif marker.role == "TL":
            X_TL = marker.x
            Y_TL = marker.y
        elif marker.role == "TR":
            X_TR = marker.x
            Y_TR = marker.y

    #Computing the average Rx ("Twist") angle, seen from top and bottom
    B_Rx_rad = math.atan((Y_BL-Y_BR)/(X_BR-X_BL))
    B_Rx_deg = math.degrees(B_Rx_rad)
    A_Rx_rad = math.atan((Y_TL-Y_TR)/(X_TR-X_TL))
    A_Rx_deg = math.degrees(A_Rx_rad)
    Rx_offset = round(abs((B_Rx_deg + A_Rx_deg) / 2), 1)

    #Center of RoI given by the 4 markers' coordinates
    RoI_x = round(np.mean([X_BL, X_BR, X_TL, X_TR]), 0)
    RoI_y = round(np.mean([Y_BL, Y_BR, Y_TL, Y_TR]), 0)

    # ret, img = cap.read()
    # RoIcenter = (RoI_x, RoI_y)
    # cv2.circle(img, RoIcenter, 5, (0, 0, 255), -1)

    return Rx_offset, RoI_x, RoI_y  

if __name__ == "__main__":

    a_thresh = 1    #1degree angular threshold
    
    intro_soft()
    marker_list = NewAcquisition()

    Rx_offset, RoI_x, RoI_y = Rx_Feedback(marker_list)

    print(f"Twist camera along Rx = {Rx_offset} degrees")
    if abs(Rx_offset) > 1:
        print(f"Twist camera along Rx by {Rx_offset} degrees")

    print("----Final Marker list----")
    for marker in marker_list:
        print(marker)
