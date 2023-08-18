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

    satisfaction = GetSatisfaction(marker_list, corr_metrics)

    return marker_list, corr_metrics, satisfaction


def countIsValid(marker_list):

    return True


def ReadMarkers():

    marker_list = []
    corr_metrics = []

    return marker_list, corr_metrics


def GetSatisfaction(marker_list, corr_metrics):

    satisfaction = 0

    return satisfaction



def IntroSoft():
    '''
    This function will take ... as an input and ouput ...s
    '''
    
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
            print("Let's start tuning !")
        if count >= 10:
            print("Maximum amount of setup procedures !")
            sys.exit(1)

        WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage)
        Timer()
        marker_list, corr_metrics, satisfaction = NewAcquisition()