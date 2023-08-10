# Script by Nicolas Robson, under supervision of Cyril Monette 2023 EPFL
# Based on an OpenCV script by Sergio Canu (pysource.com)
# 
# This script enables detecting Aruco markers OF A SPECIFIC SIZE (proportions).
# It will open the (specified #) camera for real time analysis
# Press "Esc" (27th key of keyboard) to kill program.
#
# make sure you have OpenCv-contrib installed
# $pip install opencv-contrib-python
#
# Thanks and full credits to pysource.com for the computer vision part
# https://www.youtube.com/watch?v=lbgl2u6KrDU
#
# Further informations by Core Electronics https://www.youtube.com/watch?v=Qf55aUgfLfQ
#
#
import cv2
from object_detector import *
import numpy as np

# Load Aruco detector
parameters = cv2.aruco.DetectorParameters_create()
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)


# Load Object Detector
detector = HomogeneousBgDetector()

# Load Footage 
#Cap (if using a camera)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#Image Loading (if using a single image)
#img = cv2.imread("phone_aruco_marker.jpg")   #define image to analyse

#Aruco Marker list
# marker_list = []

def read_markers() :

    while True:
        _, img = cap.read()

        # Get Aruco marker
        corners, marker_id, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)
        if corners:

            # Draw polygon around the marker
            int_corners = np.intp(corners)
            cv2.polylines(img, int_corners, True, (0, 255, 0), 5)

            #contours = detector.detect_objects(img)

            # Draw objects boundaries
            for cnt in int_corners:
                # Get rect
                rect = cv2.minAreaRect(cnt)
                (x, y), (w, h), angle = rect
                # Selecting number of significant digits and pushing into list
                x_rounded = round(x,3)
                y_rounded = round(y,3)
                marker_list.append((x_rounded, y_rounded))
                #print (marker_id[cnt][0]) #doesn't work
                # Display rectangle
                box = cv2.boxPoints(rect)
                box = np.intp(box)

                cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)

        cv2.imshow("Image", img)
        key = cv2.waitKey(10000)        #take a new picture every 10 000ms
        if key == 27:
            break

    #Print center coordinates of markers
    for val in marker_list:
        print(val, end=" ")

    cap.release()
    cv2.destroyAllWindows()

# def logic(marker_list_) :
    
#     for val in marker_list_:
#         print(val, end=" ")

if __name__ == "__main__":

    marker_list = []
    marker_list = read_markers()
    #logic(marker_list)
#     while
#     take_image
#     centred <0 detect markers
#     logic()


