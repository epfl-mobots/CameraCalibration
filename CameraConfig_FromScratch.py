import cv2
import numpy as np
import keyboard
import time
import math
import sys
from shapely.geometry import Polygon
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



def NewAcquisition(setup_stage):

    marker_list, corr_metrics = ReadMarkers(setup_stage)

    while not countIsValid(marker_list):
        count = count + 1
        if count >= 5:
            print("Too many errors counting markers.")
            sys.exit(1)
        else:
            marker_list = ReadMarkers(setup_stage)

    #Now that we are sure to have a valid New Acquisition, we can compute the overall satisfaction index
    satisfaction, _ = GetSatisfaction(marker_list, corr_metrics)
    print("Valid Acquisition")

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


def ReadMarkers(setup_stage):

    marker_list = []
    corr_metrics = []

    # Test
    marker1 = Marker(0, 0, 1)
    marker2 = Marker(9, 1, 2)
    marker3 = Marker(10, 11, 3)
    marker4 = Marker(0, 10, 4)
    marker_list = [marker1, marker2, marker3, marker4]

    #To fill last

    corr_metrics = GetCorrMetrics(marker_list, setup_stage)

    #Print visual guides (RoI center, rectangular aligners...)

    return marker_list, corr_metrics


def GetCorrMetrics(marker_list, setup_stage):

    image_width = 1280         #Decided at top of script, to help recognize markers better.
    image_height = 720         #Decided at top of script, to help recognize markers better.
    a_thresh = 1               #1deg angular threshold
    p_thresh = 10              #10pixels rotation effective offset threshold
    percent_thresh = 0.02      #2% percentage threshold
    scale_thresh_min = 0.95    #Ratio of acceptable detected RoI area / theoretical "Ideal" RoI area, min
    scale_thresh_max = 1.05    #Ratio of acceptable detected RoI area / theoretical "Ideal" RoI area, max
    Hor_FoV = 42               #Horizontal field of view of camera used, in degrees

    corr_metrics = []

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


    #Center of RoI given by the 4 markers' coordinates
    RoI_x = round(np.mean([X_BL, X_BR, X_TL, X_TR]), 0)
    RoI_y = round(np.mean([Y_BL, Y_BR, Y_TL, Y_TR]), 0)
    RoIcenter = (RoI_x, RoI_y)

    corr_metrics.append(RoIcenter)

    #Computing the average Rx ("Twist") angle, seen from top and bottom
    if setup_stage == 1 :
        B_Rx_rad = math.atan((Y_BL-Y_BR)/(X_BR-X_BL))
        B_Rx_deg = math.degrees(B_Rx_rad)
        A_Rx_rad = math.atan((Y_TL-Y_TR)/(X_TR-X_TL))
        A_Rx_deg = math.degrees(A_Rx_rad)

        Rx_offset = round(abs((B_Rx_deg + A_Rx_deg) / 2), 1)
        Rx_corr_needed = False

        if (abs(Rx_offset) > a_thresh):
            Rx_corr_needed = True

        corr_metrics.append(Rx_corr_needed)
        corr_metrics.append(Rx_offset)

    #Deciding weither a correction has to be made (Ry)
    elif setup_stage == 2 :
        Ry_corr_needed = False
        Ry_pixel_offset = RoI_x - image_width/2
        Ry_corr_angle = math.atan(Ry_pixel_offset/(0.5*image_width*math.tan(math.radians(Hor_FoV/2))))   #Exact correction angle using the camera field of view angles
        Ry_corr_angle = math.degrees(Ry_corr_angle)

        if (abs(Ry_corr_angle) > a_thresh):
            Ry_corr_needed = True

        corr_metrics.append(Ry_corr_needed)
        corr_metrics.append(Ry_corr_angle)

    #Computing the average Rz persepctive-induced angle, seen on both vedrtical sides.
    elif setup_stage == 3 :
        B_Rz_rad = math.atan((X_TL-X_BL)/(Y_BL-Y_TL))
        B_Rz_deg = math.degrees(B_Rz_rad)
        A_Rz_rad = math.atan((X_BR-X_TR)/(Y_BR-Y_TR))
        A_Rz_deg = math.degrees(A_Rz_rad)

        Rz_offset_index = round(abs((B_Rz_deg + A_Rz_deg) / 2), 1)
        Rz_corr_needed = False

        if (abs(Rz_offset_index) > 3*a_thresh):
            Rz_corr_needed = True

        corr_metrics.append(Rz_corr_needed)
        corr_metrics.append(Rz_offset_index)

    elif setup_stage == 4 :
        Ty_corr_needed = False
        Ty_pixel_offset = RoI_y - image_height/2
        Ty_corr_percent = Ty_pixel_offset/image_height

        if (abs(Ty_corr_percent) > percent_thresh):
            Ty_corr_needed = True

        corr_metrics.append(Ty_corr_needed)
        corr_metrics.append(Ty_corr_percent)

    elif setup_stage == 5 :
        Tx_corr_needed = False
        _, scale_factor = GetSatisfaction(marker_list, corr_metrics)
        if (scale_factor > scale_thresh_max):
            Tx_corr_needed = True
        if (scale_factor < scale_thresh_min):
            Tx_corr_needed = True

        corr_metrics.append(Tx_corr_needed)
        corr_metrics.append(scale_factor)

    #Corr_metrics contains [RoIcenter, Rx_corr_needed, Rx_offset, Ry_corr_needed, Ry_pixel_offset, ...]
    return corr_metrics


def GetSatisfaction(marker_list, corr_metrics):
    #Hard coding our ideal frame
    Ideal_TL = Marker(0, 0, 1)
    Ideal_TR = Marker(10, 0, 2)
    Ideal_BR = Marker(10, 10, 3)
    Ideal_BL = Marker(0, 10, 4)
    IdealFrame_marker_list = [Ideal_TL, Ideal_TR, Ideal_BR, Ideal_BL]

    # Define the custom order using a dictionary
    role_order = {"BL": 1, "BR": 2, "TR": 3, "TL": 4}

    # Use the dictionary in a lambda function to sort the lists
    sorted_markers = sorted(marker_list, key=lambda marker: role_order.get(marker.role, 5))
    sorted_ideal_markers = sorted(IdealFrame_marker_list, key=lambda marker: role_order.get(marker.role, 5))

    # Form detected and ideal polygons using the sorted lists
    detected_polygon = Polygon([(marker.x, marker.y) for marker in sorted_markers])
    ideal_polygon = Polygon([(marker.x, marker.y) for marker in sorted_ideal_markers])
    
    if not detected_polygon.is_valid:
        print("Detected polygon is invalid!")
        sys.exit(1)
    if not ideal_polygon.is_valid:
        print("Ideal polygon is invalid!")
        sys.exit(1)

    #Scale factor
    scale_factor = detected_polygon.area/ideal_polygon.area

    # Calculate the overlapping/union area
    intersection_area = detected_polygon.intersection(ideal_polygon).area
    union_polygon = detected_polygon.union(ideal_polygon)
    union_area = union_polygon.area

    # Calculate satisfaction as the ratio of overlap to ideal area
    satisfaction = intersection_area / union_area

    return satisfaction, scale_factor


def IntroSoft():

    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")
    print("To continue, press 'C' on the keyboard (key #67).")
  
    while True:
        event = keyboard.read_event()
        
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'c':
                 return



def WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage):

    message = ""
    
    if setup_stage == 0:
        message = "Let's fix each DoF one by one."
        return

    if corr_metrics[1]==True:   #If a correction is needed

        if setup_stage == 1:    #(Rx)
            message = f"Let's fix the Rx ('Twist') angle by {corr_metrics[2]} degrees."
        
        if setup_stage == 2:    #(Ry)
            message = f"Let's fix the Ry ('horizontal') angle by {corr_metrics[2]} degrees."
        
        if setup_stage == 3:    #(Rz)
            message = f"Let's fix the Rz ('vertical') angle (correction index value is {corr_metrics[2]} )."

        if setup_stage == 4:    #(Ty)
            message = f"Let's fix the Ty ('vertical') height by approximatly {corr_metrics[2]*100} % of image size."

        if setup_stage == 5:    #(Tx)
            if corr_metrics[2]>1:
                dir = f"Backwards"
            else : 
                dir = f"Forward"
            message = f"Let's fix the Tx (Back/Forth) distance moving camera holder {dir} a little."

    print(message)

    return 



def Timer():

    return



if __name__ == "__main__":

    a_thresh = 1    #1deg angular threshold
    p_thresh = 10   #10pixel angular thresh
    min_satisfaction = 0.9
    setup_stage = 0 #1(Rx),2(Ry),3(Rz),4(Ty),5(Tx) corresponding to each DOF currently being tuned, is ->0 when Tx is "Tuned"
    count = 0

    IntroSoft()
    marker_list, corr_metrics, satisfaction = NewAcquisition(setup_stage)
    
    while (satisfaction < min_satisfaction):
        count = count + 1
        if setup_stage == 0:
            print("Let's (re)start a tuning cycle !")
        if count >= 10:
            print("Maximum amount of setup procedures !")
            sys.exit(1)

        WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage)
        Timer()
        print(f"Satisfaction is {satisfaction} .")
        marker_list, corr_metrics, satisfaction = NewAcquisition(setup_stage)

        print(f"Correction metrics at count # {count}.")
        print(corr_metrics)


    print(corr_metrics)
    print(f"----Final satisfaction is {satisfaction}----")
