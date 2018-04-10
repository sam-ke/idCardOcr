# -*- coding: utf-8
import cv2
import numpy as np


im = cv2.imread('D:\OCR\p\w27.jpg')

gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
ret, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
cv2.namedWindow('binary', cv2.WINDOW_NORMAL)

cv2.imshow('binary', binary)
cv2.waitKey(0)

# 1. 查找轮廓
contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
for i in range(len(contours)):
    #cnt = contours[i]
    # area = cv2.contourArea(cnt)
    # # 面积小的都筛选掉
    # if (area < 100):
    #     continue

    # 找到最小的矩形，该矩形可能有方向
    # rect = cv2.minAreaRect(cnt)
    # # print "rect is: "
    # # print rect
    #
    # # box是四个点的坐标
    # box = cv2.cv.BoxPoints(rect)
    # box = np.int0(box)

    x, y, w, h = cv2.boundingRect(contours[i])
    cv2.rectangle(im, (x, y), (w, h), (255, 0, 0), 3)
    #cv2.drawContours(im, [box], 0, (0, 255, 0), 3)

cv2.namedWindow('canny', cv2.WINDOW_NORMAL)

cv2.imshow('canny', gray)
cv2.waitKey(0)

cv2.imshow('canny', im)
cv2.waitKey(0)