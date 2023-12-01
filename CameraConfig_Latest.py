import cv2
import numpy as np
import time
import math
import sys
from shapely.geometry import Polygon
from object_detector import *
from picamera2 import Picamera2, Preview
from marker import Marker


IMAGE_WIDTH = 4608
IMAGE_HEIGHT = 2592
A_THRESH = 1
P_THRESH = 10
PERCENT_THRESH = 0.02
SCALE_THRESH_MIN = 0.95
SCALE_THRESH_MAX = 1.05
HOR_FoV = 42
N_MARKERS = 4  # Expected number of markers

# Hard coded ideal frame, BEWARE !
IdealFrame_marker_list = [
    Marker(461, 260, 1),    # TL
    Marker(4147, 260, 2),   # TR
    Marker(4147, 2333, 3),  # BR
    Marker(461, 2333, 4)    # BL
    ]

# Load Aruco detector
parameters = cv2.aruco.DetectorParameters_create()
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)

# Load Object Detector
detector = HomogeneousBgDetector()

# Camera object
picam2 = Picamera2()


def GetValidAcquisition():
    '''
    Acquires images until a valid one is found and returns the list of markers.
    '''

    valid_img = False
    while not valid_img:
        img = ImageAcquisition()
        marker_list = ReadMarkers(img)
        
        valid_img = countIsValid(marker_list)
        
        time.sleep(0.3)  # Wait for 0.75 seconds before trying again

    print("Valid Acquisition")

    return img, marker_list



def countIsValid(marker_list):
    '''
    Verifies that the right number of markers were detected in marker_list.
    '''
    
    marker_count = len(marker_list)

    if marker_count == 0:
        print("No markers detected.")
        return False
    elif marker_count != N_MARKERS:
        print(f"Detected {marker_count} markers but expected {N_MARKERS}.")
        return False
    else:
        return True

def InitCamera():
    config=picam2.create_still_configuration()
    print(config)
    picam2.configure(config)
    picam2.start()
    time.sleep(1)
    print("Camera configured")

    return

def ImageAcquisition():
    '''
    Makes the acquisition of  a picture from the RPi Cam v3. 
    TODO: Implement the acquisition from the RPi Cam v3.
    '''
    picture = picam2.capture_array()
    
    return picture

def drawFeedback(img, marker_list, message):     # add corr_metrics if drawing visual feedback
    '''
    Draws the feedback image.
    '''

    # Assuming you will implement visual guides later based on the comment
    # Print visual guides (RoI center, rectangular aligners...)

    for marker in marker_list:
        cv2.putText(img, "ID: " + str(marker.ID), (marker.x - 20, marker.y + 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        cv2.circle(img, (marker.x, marker.y), 10, (0, 0, 255), -1)
    for marker in IdealFrame_marker_list:
        cv2.putText(img, "Ideal " + str(marker.role), (marker.x - 20, marker.y + 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        cv2.circle(img, (marker.x, marker.y), 10, (0, 0, 255), -1)
        
    #Printing message directly on image
    cv2.putText(img, message, (500, 500), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
    
    # Resizing feedback image not to be bigger than the screen used (defaulted to UHD)
    img_resized = cv2.resize(img, (1920, 1080))
    cv2.imshow(winname="Feedback image", mat=img_resized)
    cv2.waitKey(10)
        
        
    print(f"Feedback image drawn ({len(marker_list)} markers)", img.shape)

    return


def ReadMarkers(img):
    '''
    Reads the markers from the image and returns a list of markers.
    '''
    marker_list = []

    # Detect Aruco markers
    marker_corners, ids, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)
    
    if ids is not None:
        for i, corners in enumerate(marker_corners):
            corners_int = np.int32(corners)
            center = tuple(np.mean(corners_int[0], axis=0).astype(int)) # double list within int_corner si we do int_corner[0] to get rid of the outer list
            marker = Marker(center[0], center[1], ids[i][0])
            marker_list.append(marker)


    # corr_metrics = GetCorrMetrics(marker_list, setup_stage) if countIsValid(marker_list) else [] to be used elsewhere

    return marker_list


def calculate_angle(dx, dy):
    return math.degrees(math.atan(dy / dx))

def GetCorrMetrics(marker_list, setup_stage):
    '''
    Computes the correction metrics based on the detected markers.
    :return: A list of correction metrics [(RoI_x, RoI_y), calibration_needed, correction_value]
    '''
    markers = {m.role: (m.x, m.y) for m in marker_list}
    RoI_x = round(np.mean([x for x, _ in markers.values()]), 0)
    RoI_y = round(np.mean([y for _, y in markers.values()]), 0)
    RoIcenter = (RoI_x, RoI_y)
    corr_metrics = [RoIcenter]

    if setup_stage == 0:
        B_Rx_deg = calculate_angle(markers['BR'][0] - markers['BL'][0], markers['BL'][1] - markers['BR'][1])
        A_Rx_deg = calculate_angle(markers['TR'][0] - markers['TL'][0], markers['TL'][1] - markers['TR'][1])
        Rx_offset = round(abs((B_Rx_deg + A_Rx_deg) / 2), 1)
        corr_metrics.extend([Rx_offset > A_THRESH, Rx_offset])

    elif setup_stage == 1:
        Ry_pixel_offset = RoI_x - IMAGE_WIDTH/2
        Ry_corr_angle = math.degrees(math.atan(Ry_pixel_offset / (0.5 * IMAGE_WIDTH * math.tan(math.radians(HOR_FoV/2)))))
        Ry_corr_angle = round(Ry_corr_angle, 1)
        corr_metrics.extend([abs(Ry_corr_angle) > A_THRESH, Ry_corr_angle])

    elif setup_stage == 2:
        B_Rz_deg = calculate_angle(markers['TL'][0] - markers['BL'][0], markers['BL'][1] - markers['TL'][1])
        A_Rz_deg = calculate_angle(markers['BR'][0] - markers['TR'][0], markers['BR'][1] - markers['TR'][1])
        Rz_offset_index = round(abs((B_Rz_deg + A_Rz_deg) / 2), 1)
        corr_metrics.extend([Rz_offset_index > (3 * A_THRESH), Rz_offset_index])

    elif setup_stage == 3:
        Ty_pixel_offset = RoI_y - IMAGE_HEIGHT/2
        Ty_corr_percent = Ty_pixel_offset/IMAGE_HEIGHT
        corr_metrics.extend([abs(Ty_corr_percent) > PERCENT_THRESH, Ty_corr_percent])

    elif setup_stage == 4:
        _, scale_factor = GetSatisfaction(marker_list)
        Tx_corr_needed = scale_factor < SCALE_THRESH_MIN or scale_factor > SCALE_THRESH_MAX
        corr_metrics.extend([Tx_corr_needed, scale_factor])

    return corr_metrics



def GetSatisfaction(marker_list):
    '''
    Computes a satisfaction metric based on the detected markers and the ideal markers.
    '''

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

    print(f"Satisfaction metric of image is {satisfaction}")
    return satisfaction, scale_factor

def Intro():
    print("Hello, welcome to this camera setup assistant.")
    print("Please make sure you are roughly aligned with the markers and the 4 are visible, before continuing.")


def SendInstructions(img, corr_metrics, setup_stage):
    """
    Walks through the setup stages and suggests necessary corrections based on the given metrics.
    
    :param corr_metrics: Metrics that indicate the corrections required
    :param setup_stage: Current stage of the setup
    
    :return: Updated setup stage and wether a correction is needed
    """

    messages = {
        0: f"Let's fix the Rx ('Twist') angle by {corr_metrics[2]} degrees.",
        1: f"Let's fix the Ry ('horizontal') angle by {corr_metrics[2]} degrees.",
        2: f"Let's fix the Rz ('vertical') angle (correction index value is {corr_metrics[2]}).",
        3: f"Let's fix the Ty ('vertical') height by approximately {corr_metrics[2]*100} % of image size.",
    }

    if corr_metrics[1]:  # If a correction is needed
        message = messages.get(setup_stage)
        if setup_stage == 4:
            dir = "Backwards" if corr_metrics[2] > 1 else "Forwards"
            message = f"Let's fix the Tx (Back/Forth) distance by moving the camera holder {dir}."
        print(message)
    else:
        message = f"No message"
        return (setup_stage + 1), False, message 
        
    if message is None:
        message = f"No message"

    # drawFeedback(img, marker_list) # To be implemented later

    return setup_stage, corr_metrics[1], message

#-----------------------------------------------------------------

if __name__ == "__main__":

    satisfaction = 0
    setup_stage = 0
    perfect_run = False
    marker_list = []

    Intro()
    InitCamera()

    try:
        #img =
        #cv2.show(img)
        
        while not perfect_run:
            perfect_run = True # Any error will set this to False

            while setup_stage < 5:
                img, marker_list = GetValidAcquisition()
                satisfaction, _ = GetSatisfaction(marker_list)

                corr_metrics = GetCorrMetrics(marker_list, setup_stage)
                setup_stage, change_needed, message = SendInstructions(img, corr_metrics, setup_stage)

                if change_needed:
                    perfect_run = False

                time.sleep(0.3)
                drawFeedback(img, marker_list, message)  # Could add corre_metrics for visual feedback

            setup_stage = 0
        
        satisfaction, _ = GetSatisfaction(marker_list)
        print(f"----Final satisfaction is {satisfaction}----")

    except KeyboardInterrupt:
        print("Camera calibration process stopped by user - ctrl-c pressed.")
    finally:
        cv2.destroyAllWindows()
