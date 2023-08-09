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

contours = detector.detect_objects(img)
print(contours)

#Show image
cv2.imshow("Image",img)     #show image
cv2.waitKey(0)              #in a timeless window