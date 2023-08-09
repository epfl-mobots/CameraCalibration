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
for cnt in contours:    #for as many "interesting" contours it finds
    #Get a precise contour
    #cv2.polylines(img, [cnt], True, (255, 0, 0), 2)  #The polylines function will draw a polygon joining each "corner" point. "True" for closing the polygon, "2" for 2 pixel thick
    
    #Get a rectangular contour
    rect = cv2.minAreaRect(cnt)
    (x, y), (w, h), angle = rect       #(x, y) center of object, (w, h) dimensions in pixels of object

    box = cv2.boxPoints(rect)
    box = np.int0(box)      #Does conversion between float to int so OpenCV doesn't have an error
    
    #Draws a circle around center of object
    cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)   #Using int() so we don't have errors drawing when coordinates are not integers.
    #Draws a box around object using corners
    cv2.polylines(img, [box], True, (255, 0, 0), 2)
    #Add text sith dimensions, using round(value,number of decimals)
    cv2.putText(img, "Width{}".format(round(w,1)), (int(x -100), int(y +15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)
    cv2.putText(img, "Height{}".format(round(w,1)), (int(x -100), int(y -15)), cv2.FONT_HERSHEY_PLAIN, 1, (100, 200, 0), 2)

    print(box)
    #print(x, y)     #(x, y) Coordinates of the center of the object detected
    #print(w, h)
    #print(angle)


#Show image
cv2.imshow("Image",img)     #show image
cv2.waitKey(10000)              #in a 10s window (put 0 for infinite)
