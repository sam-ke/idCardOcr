# -*- coding: utf-8 -*-

import numpy as np
import cv2
import json
import os
import sys
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-sf', metavar='scaleFactor', help='specifying how much the image size is reduced at each image scale.', default='1', type=int, choices=[1,2,3,4,5,6,7,8,9])
parser.add_argument('-mn', metavar='minNeighbors', help='specifying how many neighbors each candidate rectangle should have to retain it.', default='5', type=int)
parser.add_argument('image', help='path to image file')
args = parser.parse_args()


if getattr(sys, 'frozen', False):
	curpath = os.path.dirname(sys.executable)
elif __file__:
	curpath = os.path.dirname(os.path.realpath(__file__))

pathtoimg = args.image
if not os.path.isfile(pathtoimg):
	sys.exit("you neeed provid a valid imgfile")


def _checkShape(img, pt, w, h):
	shape = img.shape
	max_h, max_w, y = shape
	xx = pt[0] - w/3
	yy = pt[1] - h/3
	new_x = xx if xx > 0 else 0
	new_y = yy if yy > 0 else 0
	ww = pt[0] + w + w/3
	hh = pt[1] + h + h/3
	new_w = ww if ww < max_w else max_w - 1
	new_h = hh if hh < max_h else max_h - 1

	return (new_x, new_y), new_w, new_h


face_cascade = cv2.CascadeClassifier(os.path.join(curpath, 'haarcascade_frontalface_default.xml'))
#eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')

img = cv2.imread(pathtoimg)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

lis = []
sf = 1 + args.sf/10.0
faces = face_cascade.detectMultiScale(gray, sf, args.mn)
for (x,y,w,h) in faces:
	pt, w, h = _checkShape(img, (x,y), w, h)
	#cv2.rectangle(img, (x,y), (x+w, y+h),(255,0,0),2)
	lis.append([pt[0], pt[1], w, h])
	#print x, y, x+w, y+h
#cv2.imwrite('face.jpg', img)
#cv2.waitKey(0)
#cv2.destroyAllWindows()

print json.dumps(lis, sort_keys=True)
