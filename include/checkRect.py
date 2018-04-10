# -*- coding: utf8
import sys
import cv2
import numpy as np
from matplotlib import pyplot as plt


"""
检测图片中最大的四边形区域并裁剪
"""


class Line:

    def __init__(self, l):
        self.point = l
        x1, y1, x2, y2 = l
        self.c_x = (x1 + x2) / 2
        self.c_y = (y1 + y2) / 2


def show(im):
    msg = 'press any key to continue'
    cv2.namedWindow(msg, cv2.WINDOW_NORMAL)
    cv2.imshow(msg, im)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def intersection(l1, l2):
    x1, y1, x2, y2 = l1.point
    x3, y3, x4, y4 = l2.point
    a1, b1 = y2 - y1, x1 - x2
    c1 = a1 * x1 + b1 * y1
    a2, b2 = y4 - y3, x3 - x4
    c2 = a2 * x3 + b2 * y3
    det = a1 * b2 - a2 * b1
    assert det, "lines are parallel"
    return (1. * (b2 * c1 - b1 * c2) / det, 1. * (a1 * c2 - a2 * c1) / det)


def scannerLite(im, debug=False):
    # resize
    h, w, _ = im.shape
    min_w = 200
    scale = min(10., w * 1. / min_w)
    h_proc = int(h * 1. / scale)
    w_proc = int(w * 1. / scale)
    im_dis = cv2.resize(im, (w_proc, h_proc))

    # gray
    gray = cv2.cvtColor(im_dis, cv2.COLOR_BGR2GRAY)

    # blur
    #gray = cv2.blur(gray, (3, 3))
    #gray = cv2.GaussianBlur(gray, (3,3), 0)

    # canny edges detection
    high_thres = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[0]
    low_thres = high_thres * 0.5
    canny = cv2.Canny(gray, low_thres, high_thres)
    if debug:
        show(canny)

    # lines detection
    lines = cv2.HoughLinesP(
        canny, 1, np.pi / 180, w_proc / 6, None, w_proc / 6, 20)

    if debug:
        t = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)

    # classify lines
    hori, vert = [], []

    for l in lines[0]:
        x1, y1, x2, y2 = l
        if abs(x1 - x2) > abs(y1 - y2):
            hori.append(Line(l))
        else:
            vert.append(Line(l))
        if debug:
            cv2.line(t, (x1, y1), (x2, y2), (0, 0, 255), 1)
    if debug:
        show(t)

    # not enough
    if len(hori) < 2:
        if not hori or hori[0].c_y > h_proc / 2:
            hori.append(Line((0, 0, w_proc - 1, 0)))
        if not hori or hori[0].c_y <= h_proc / 2:
            hori.append(Line((0, h_proc - 1, w_proc - 1, h_proc - 1)))

    if len(vert) < 2:
        if not vert or vert[0].c_x > w_proc / 2:
            vert.append(Line((0, 0, 0, h_proc - 1)))
        if not vert or vert[0].c_x <= w_proc / 2:
            vert.append(Line((w_proc - 1, 0, w_proc - 1, h_proc - 1)))

    hori.sort(key=lambda l: l.c_y)
    vert.sort(key=lambda l: l.c_x)

    # corners
    if debug:
        for l in [hori[0], vert[0], hori[-1], vert[-1]]:
            x1, y1, x2, y2 = l.point
            cv2.line(t, (x1, y1), (x2, y2), (0, 255, 255), 1)

    img_pts = [intersection(hori[0], vert[0]), intersection(hori[0], vert[-1]),
               intersection(hori[-1], vert[0]), intersection(hori[-1], vert[-1])]

    for i, p in enumerate(img_pts):
        x, y = p
        img_pts[i] = (x * scale, y * scale)
        if debug:
            cv2.circle(t, (int(x), int(y)), 1, (255, 255, 0), 3)
    if debug:
        show(t)

    # perspective transform
    w_a4, h_a4 = 1654, 2339
    #w_a4, h_a4 = 600, 800
    dst_pts = np.array(
        ((0, 0), (w_a4 - 1, 0), (0, h_a4 - 1), (w_a4 - 1, h_a4 - 1)),
        np.float32)
    img_pts = np.array(img_pts, np.float32)
    print img_pts
    transmtx = cv2.getPerspectiveTransform(img_pts, dst_pts)
    return cv2.warpPerspective(im, transmtx, (w_a4, h_a4))


if __name__ == '__main__':
    im = cv2.imread('D:\OCR\p\w32.jpg')
    show(im)
    dst = scannerLite(im, debug=True)
    show(dst)