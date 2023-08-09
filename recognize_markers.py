# Scipt by Nicolas Robson, under supervision of Cyril Monette 2023
# Thanks and full credits to pysource.com for the computer vision part

# make sure you have OpenCv contrib installed
# $pip install opencv-contrib-python
print("hello")

import cv2
from object_detector import *   #import everything

img = cv2.imread("phone.jpg")   #define image to analyse

#Load Object Detector
detector = HomogeneousBgDetector()

contours = detector.detect_objects(img)     #gives object boundary corners
#print(contours)

#Draw object boundaries
for cnt in contours:
    #Get a precise contour
    cv2.polylines(img, [cnt], True, (255, 0, 0), 2)  #The polylines function will draw a polygon joining each "corner" point. "True" for closing the polygon, "2" for 2 pixel thick
    #Get a rectangular contour
    (x, y), (w, h), angle = cv2.minAreaRect(cnt)

    cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)   #Using int() so we don't have errors drawing when coordinates are not integers.
    print(x, y)     #(x, y) Coordinates of the center of the object
    print(w, h)
    print(angle)


#Show image
cv2.imshow("Image",img)     #show image
cv2.waitKey(0)              #in a timeless window