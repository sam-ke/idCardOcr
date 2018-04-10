# -*- coding: utf8
"""
canny算子
"""

import cv2
import numpy as np
from matplotlib import pyplot
import functions as func

# 加载图片
img = cv2.imread(r'D:\OCR\p\test.jpg')

x = cv2.Sobel(img, cv2.CV_16S, 1, 0)
y = cv2.Sobel(img, cv2.CV_16S, 0, 1)

absX = cv2.convertScaleAbs(x)  # 转回uint8
absY = cv2.convertScaleAbs(y)

dst = cv2.addWeighted(absX, 0.5, absY, 0.5, 0)

func.showImg(absX, 'absX')
func.showImg(absY, 'absY')
func.showImg(dst, 'Result')

cv2.destroyAllWindows()