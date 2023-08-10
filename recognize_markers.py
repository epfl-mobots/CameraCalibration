# Script by Nicolas Robson, under supervision of Cyril Monette 2023
# Thanks and full credits to pysource.com for the computer vision part

# make sure you have OpenCv-contrib installed
# $pip install opencv-contrib-python
print("Hello, welcome to this camera-alignment process assistant.")

import numpy as np
import cv2
from object_detector import *   #import everything

# Load Aruco detector
parameters = cv2.aruco.DetectorParameters_create()     #Detect Aruco market function
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)    #Dictionary to detect marker given it's size-----/!\
aruco_size = 5.0     # To change depending on marker used. Here it's for a 50mm side-square aruco marker. 
#Load Object Detector
detector = HomogeneousBgDetector()  #This detector is for a continous backgriund, beware /!\
#Load footage to read
img = cv2.imread("phone_aruco_marker.jpg")   #define image to analyse

# Program loop

#Detect Aruco markers and draw polygon
corners, _, _ = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)   #Gives marker corners-> corners, _'s are unused parameters
#Note that if multiple markers are detected, 'corners' becomes a list with each marker accessible via
int_corners = np.int0(corners)
cv2.polylines(img, int_corners[0], True, (0, 255, 0), 5)   #First detected marker
#print(corners)

#Pixel to cm conversion
aruco_perimeter = cv2.arcLength(corners[0], True)
#print(aruco_perimeter)
pixel_cm_ratio = aruco_perimeter / (4*aruco_size)
#print(pixel_cm_ratio)

#Detect all nearby objects
contours = detector.detect_objects(img)     #Gives object boundary corners
#print(contours)

#Draw object boundaries
for cnt in contours:    #for as many "interesting" contours it finds
    #Get a precise contour
    #cv2.polylines(img, [cnt], True, (255, 0, 0), 2)  #The polylines function will draw a polygon joining each "corner" point. "True" for closing the polygon, "2" for 2 pixel thick
    
    #Get a tight rectangular contour around marker
    rect = cv2.minAreaRect(cnt)
    (x, y), (w, h), angle = rect       #(x, y) center of object, (w, h) dimensions in pixels of object
    
    box = cv2.boxPoints(rect)
    box = np.int0(box)      #Does conversion between float to int so OpenCV doesn't have an error


    #Applying pixel to cm conversion
    object_width = w / pixel_cm_ratio
    object_height = h / pixel_cm_ratio
    
    #Draws a circle around center of object
    cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)   #Using int() so we don't have errors drawing when coordinates are not integers.
    #Draws a box around object using corners
    cv2.polylines(img, [box], True, (255, 0, 0), 2)
    #Add text sith dimensions, using round(value,number of decimals)
    #In Pixels
    #cv2.putText(img, "Width {}".format(round(w,1)), (int(x -100), int(y +15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
    #cv2.putText(img, "Height {}".format(round(h,1)), (int(x -100), int(y -15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
    #In cm
    cv2.putText(img, "Width {} cm".format(round(object_width,1)), (int(x -100), int(y +15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
    cv2.putText(img, "Height {} cm".format(round(object_height,1)), (int(x -100), int(y -15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

    print(box)
    #print(x, y)     #(x, y) Coordinates of the center of the object detected
    #print(w, h)
    #print(angle)

#Show image
cv2.imshow("Image",img)     #show image
cv2.waitKey(10000)              #in a 10s window (put 0 for infinite)
