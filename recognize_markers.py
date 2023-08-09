# Scipt by Nicolas Robson, under supervision of Cyril Monette 2023
# Thanks and full credits to pysource.com for the computer vision part

# make sure you have OpenCv contrib installed
# $pip install opencv-contrib-python
print("hello")

import numpy as np
import cv2
from object_detector import *   #import everything

img = cv2.imread("phone.jpg")   #define image to analyse

#Load Object Detector
detector = HomogeneousBgDetector()

contours = detector.detect_objects(img)     #gives object boundary corners
#print(contours)

#Draw object boundaries
for cnt in contours:    #for as many "interesting" contours he finds
    #Get a precise contour
    #cv2.polylines(img, [cnt], True, (255, 0, 0), 2)  #The polylines function will draw a polygon joining each "corner" point. "True" for closing the polygon, "2" for 2 pixel thick
    
    #Get a rectangular contour
    rect = cv2.minAreaRect(cnt)
    (x, y), (w, h), angle = rect

    cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)   #Using int() so we don't have errors drawing when coordinates are not integers.
    
    box = cv2.boxPoints(rect)
    box = np.int0(box)      #Does conversion between float to int so OpenCV doesn't have an error
    
    cv2.polylines(img, [box], True, (255, 0, 0), 2)

    print(box)
    #print(x, y)     #(x, y) Coordinates of the center of the object detected
    #print(w, h)
    #print(angle)


#Show image
cv2.imshow("Image",img)     #show image
cv2.waitKey(0)              #in a timeless window
