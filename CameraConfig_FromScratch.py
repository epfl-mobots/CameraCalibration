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



def NewAcquisition():

    marker_list, corr_metrics = ReadMarkers()

    while not countIsValid(marker_list):
        count = count + 1
        if count >= 5:
            print("Too many errors counting markers.")
            sys.exit(1)
        else:
            marker_list = ReadMarkers()

    #Now that we are sure to have a valid New Acquisition, we can compute the overall satisfaction index
    satisfaction = GetSatisfaction(marker_list, corr_metrics)

    return marker_list, corr_metrics, satisfaction


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

    return True


def ReadMarkers():

    marker_list = []
    corr_metrics = []

    #To fill last

    corr_metrics = GetCorrMetrics(marker_list)

    #Print visual guides (RoI center, rectangular aligners...)

    return marker_list, corr_metrics


def GetCorrMetrics(marker_list):

    corr_metrics = []

    return corr_metrics



def GetSatisfaction(marker_list, corr_metrics):


    satisfaction = 0

    return satisfaction



def IntroSoft():

    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")
    print("To continue, press 'C' on the keyboard (key #67).")
  
    while True:
        event = keyboard.read_event()
        
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'c':
                 return
    
    return



def WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage):
    
    return



def Timer():

    return



if __name__ == "__main__":

    a_thresh = 1    #1deg angular threshold
    p_thresh = 10   #10pixel angular thresh
    min_satisfaction = 0.8
    setup_stage = 0 #1(Rx),2(Ry),3(Rz),4(Tz),5(Tx) corresponding to each DOF currently being tuned, is ->0 when Tx is "Tuned"
    count = 0

    IntroSoft()
    marker_list, corr_metrics, satisfaction = NewAcquisition()
    
    while (satisfaction < min_satisfaction):
        count = count + 1
        if setup_stage == 0:
            print("Let's (re)start a tuning cycle !")
        if count >= 10:
            print("Maximum amount of setup procedures !")
            sys.exit(1)

        WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage)
        Timer()
        marker_list, corr_metrics, satisfaction = NewAcquisition()
