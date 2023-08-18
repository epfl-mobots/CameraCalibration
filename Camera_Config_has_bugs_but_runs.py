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
    MAX_RETRIES = 5
    count = 0

    while True:
        marker_list, corr_metrics = ReadMarkers(setup_stage)
        
        if countIsValid(marker_list, True) or count >= MAX_RETRIES:
            break
        
        count += 1
        if count == MAX_RETRIES:
            print("Too many errors counting markers.")
            sys.exit(1)
        
        Timer()

    satisfaction, _ = GetSatisfaction(marker_list)
    print("Valid Acquisition")

    return marker_list, corr_metrics, satisfaction



def countIsValid(marker_list, text_wanted=False):
    n = 4  # Expected number of markers
    
    marker_count = len(marker_list)
    
    if marker_count == n:
        if text_wanted:
            print("Valid marker count.")
        return True

    if text_wanted:
        if marker_count == 0:
            print("Let's do our first marker reading.")
        elif marker_count < n:
            print(f"Make sure all ({n}) markers are visible by the camera. Not enough were recognized.")
        else:
            print("Error in marker recognition. Too many were recognized. Make sure the camera has proper visibility.")
    
    return False



def ReadMarkers(setup_stage):
    if not cap.isOpened():
        print("Error: Camera not initialized properly.")
        return [], []

    ret, img = cap.read()
    if not ret or img is None:
        print("Error: Failed to read frame from camera.")
        return [], []

    marker_list = []

    # Detect Aruco markers
    corners, ids, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)
    
    if ids is not None:
        for i, corner in enumerate(corners):
            int_corner = np.int32(corner)
            center = tuple(np.mean(int_corner[0], axis=0).astype(int))
            marker = Marker(center[0], center[1], ids[i][0])
            marker_list.append(marker)

            cv2.polylines(img, [int_corner], True, (0, 255, 0), 5)
            cv2.circle(img, center, 5, (0, 0, 255), -1)
            cv2.putText(img, "ID: " + str(ids[i][0]), (center[0] - 20, center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
    corr_metrics = GetCorrMetrics(marker_list, setup_stage) if countIsValid(marker_list) else []

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == 27:
        cap.release()
        cv2.destroyAllWindows()

    # Assuming you will implement visual guides later based on the comment
    # Print visual guides (RoI center, rectangular aligners...)

    return marker_list, corr_metrics



# Global constants or move these to the class level if you're using OOP
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
A_THRESH = 1
P_THRESH = 10
PERCENT_THRESH = 0.02
SCALE_THRESH_MIN = 0.95
SCALE_THRESH_MAX = 1.05
HOR_FoV = 42

def calculate_angle(dx, dy):
    return math.degrees(math.atan(dy / dx))

def GetCorrMetrics(marker_list, setup_stage):
    if not countIsValid(marker_list):
        print("Shouldn't be asking this!")
        sys.exit(1)

    markers = {m.role: (m.x, m.y) for m in marker_list}
    RoI_x = round(np.mean([x for x, _ in markers.values()]), 0)
    RoI_y = round(np.mean([y for _, y in markers.values()]), 0)
    RoIcenter = (RoI_x, RoI_y)
    corr_metrics = [RoIcenter]

    if setup_stage == 1:
        B_Rx_deg = calculate_angle(markers['BR'][0] - markers['BL'][0], markers['BL'][1] - markers['BR'][1])
        A_Rx_deg = calculate_angle(markers['TR'][0] - markers['TL'][0], markers['TL'][1] - markers['TR'][1])
        Rx_offset = round(abs((B_Rx_deg + A_Rx_deg) / 2), 1)
        corr_metrics.extend([Rx_offset > A_THRESH, Rx_offset])

    elif setup_stage == 2:
        Ry_pixel_offset = RoI_x - IMAGE_WIDTH/2
        Ry_corr_angle = math.degrees(math.atan(Ry_pixel_offset / (0.5 * IMAGE_WIDTH * math.tan(math.radians(HOR_FoV/2)))))
        corr_metrics.extend([abs(Ry_corr_angle) > A_THRESH, Ry_corr_angle])

    elif setup_stage == 3:
        B_Rz_deg = calculate_angle(markers['TL'][0] - markers['BL'][0], markers['BL'][1] - markers['TL'][1])
        A_Rz_deg = calculate_angle(markers['BR'][0] - markers['TR'][0], markers['BR'][1] - markers['TR'][1])
        Rz_offset_index = round(abs((B_Rz_deg + A_Rz_deg) / 2), 1)
        corr_metrics.extend([Rz_offset_index > (3 * A_THRESH), Rz_offset_index])

    elif setup_stage == 4:
        Ty_pixel_offset = RoI_y - IMAGE_HEIGHT/2
        Ty_corr_percent = Ty_pixel_offset/IMAGE_HEIGHT
        corr_metrics.extend([abs(Ty_corr_percent) > PERCENT_THRESH, Ty_corr_percent])

    elif setup_stage == 5:
        _, scale_factor = GetSatisfaction(marker_list)
        Tx_corr_needed = scale_factor < SCALE_THRESH_MIN or scale_factor > SCALE_THRESH_MAX
        corr_metrics.extend([Tx_corr_needed, scale_factor])

    return corr_metrics



def GetSatisfaction(marker_list):

    # If there aren't enough detected markers, return 0 satisfaction and scale.
    if not countIsValid(marker_list):
        return 0, 0

    # Define ideal frame markers
    IdealFrame_marker_list = [
        Marker(0, 0, 1),    # TL
        Marker(10, 0, 2),   # TR
        Marker(10, 10, 3),  # BR
        Marker(0, 10, 4)    # BL
    ]

    # Define the custom order using a dictionary
    role_order = {"BL": 1, "BR": 2, "TR": 3, "TL": 4}

    # Sort markers based on the custom order
    sorted_markers = sorted(marker_list, key=lambda marker: role_order.get(marker.role, 5))
    sorted_ideal_markers = sorted(IdealFrame_marker_list, key=lambda marker: role_order.get(marker.role, 5))

    # Form detected and ideal polygons using the sorted lists
    detected_polygon = Polygon([(marker.x, marker.y) for marker in sorted_markers])
    ideal_polygon = Polygon([(marker.x, marker.y) for marker in sorted_ideal_markers])

    if not detected_polygon.is_valid or not ideal_polygon.is_valid:
        print("Detected or ideal polygon is invalid!")
        sys.exit(1)

    # Calculate scale factor and satisfaction
    scale_factor = detected_polygon.area / ideal_polygon.area
    satisfaction = detected_polygon.intersection(ideal_polygon).area / detected_polygon.union(ideal_polygon).area

    return satisfaction, scale_factor



def Timer():

    wait_t = 3   #3s
    time.sleep(wait_t)
    print("New Camera footage Acquisition upcoming !")
    time.sleep(0.5*wait_t)
    
    return



def IntroSoft():
    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")
    print("To continue, press 'C' on the keyboard (key #67).")
    
    while not keyboard.is_pressed('c'):
        pass



def WalkThroughSetup(marker_list, corr_metrics, _, setup_stage):
    """
    Walks through the setup stages and suggests necessary corrections based on the given metrics.
    
    :param marker_list: List of markers
    :param corr_metrics: Metrics that indicate the corrections required
    :param _: Unused parameter (for consistency with other functions)
    :param setup_stage: Current stage of the setup
    
    :return: Updated setup stage
    """
    
    if setup_stage > 5:
        return 1

    # Safety check
    if len(corr_metrics) < 3:
        print("Error: corr_metrics doesn't have enough data!")
        return setup_stage

    messages = {
        1: f"Let's fix the Rx ('Twist') angle by {corr_metrics[2]} degrees.",
        2: f"Let's fix the Ry ('horizontal') angle by {corr_metrics[2]} degrees.",
        3: f"Let's fix the Rz ('vertical') angle (correction index value is {corr_metrics[2]}).",
        4: f"Let's fix the Ty ('vertical') height by approximately {corr_metrics[2]*100} % of image size.",
    }

    if corr_metrics[1]:  # If a correction is needed
        message = messages.get(setup_stage)
        if setup_stage == 5:
            dir = "Backwards" if corr_metrics[2] > 1 else "Forward"
            message = f"Let's fix the Tx (Back/Forth) distance by moving the camera holder {dir} a little."
        print(message)
    else:
        return setup_stage + 1

    return setup_stage

#-----------------------------------------------------------------

if __name__ == "__main__":

    min_satisfaction = 0.9
    setup_stage = 1
    max_attempts = 20

    IntroSoft()
    marker_list, corr_metrics, satisfaction = NewAcquisition(setup_stage)
    
    for attempt in range(max_attempts):
        if satisfaction >= min_satisfaction:
            break

        setup_stage = WalkThroughSetup(marker_list, corr_metrics, satisfaction, setup_stage)

        Timer()
        marker_list, corr_metrics, satisfaction = NewAcquisition(setup_stage)

    else:
        print("Maximum amount of setup procedures reached!")
        sys.exit(1)

    print(corr_metrics)
    print(f"----Final satisfaction is {satisfaction}----")


#---------------------------------------------------------------------------
#Last execution output :
# Hello, welcome to this camera setup assistant.
# Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.
# To continue, press 'C' on the keyboard (key #67).
# Let's do our first marker reading.
# New Camera footage Acquisition upcoming !
# Let's do our first marker reading.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Rx ('Twist') angle by 1.7 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Rx ('Twist') angle by 3.7 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Rx ('Twist') angle by 1.6 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by 9.47468937506772 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by 8.564759657459422 degrees.
# New Camera footage Acquisition upcoming !
# Make sure all (4) markers are visible by the camera. Not enough were recognized.
# New Camera footage Acquisition upcoming !
# Make sure all (4) markers are visible by the camera. Not enough were recognized.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by 9.701438460180064 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by 12.174067712705273 degrees.
# New Camera footage Acquisition upcoming !
# Make sure all (4) markers are visible by the camera. Not enough were recognized.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by 6.041224574091831 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ry ('horizontal') angle by -2.796413860931324 degrees.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Rz ('vertical') angle (correction index value is 88.5).
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ty ('vertical') height by approximately 8.75 % of image size.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Ty ('vertical') height by approximately 3.888888888888889 % of image size.
# New Camera footage Acquisition upcoming !
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# New Camera footage Acquisition upcoming !
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Tx (Back/Forth) distance by moving the camera holder Backwards a little.
# New Camera footage Acquisition upcoming !
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Tx (Back/Forth) distance by moving the camera holder Backwards a little.
# New Camera footage Acquisition upcoming !
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Tx (Back/Forth) distance by moving the camera holder Backwards a little.
# New Camera footage Acquisition upcoming !
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Let's fix the Tx (Back/Forth) distance by moving the camera holder Backwards a little.
# New Camera footage Acquisition upcoming !
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid marker count.
# C:\Users\41787\anaconda3\envs\CameraConfig\Lib\site-packages\shapely\set_operations.py:133: RuntimeWarning: invalid value encountered in intersection
#   return lib.intersection(a, b, **kwargs)
# Valid Acquisition
# Maximum amount of setup procedures reached!