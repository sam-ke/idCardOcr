# -*- coding: utf-8 -*-
import os, cv2
import argparse
import sys, numpy as np
#import imutils
import math
import include.binaryzation as bz
import include.functions as func
#import win32api
import copy
import json


DEBUG = False

CARD_NAME = ''
CARD_SEX = ''
CARD_ETHNIC = ''
CARD_YEAR = ''
CARD_MON = ''
CARD_DAY = ''
CARD_ADDR = ''
#身份证号码
CARD_NUM = ''



#from imutils.perspective import four_point_transform

parser = argparse.ArgumentParser()
parser.add_argument('image', help='path to image file')
args = parser.parse_args()

curpath = ''
if getattr(sys, 'frozen', False):
    curpath = os.path.dirname(sys.executable)
elif __file__:
    curpath = os.path.dirname(os.path.realpath(__file__))

pathtoimg = args.image
if not os.path.isfile(pathtoimg):
    #sys.exit("you neeed provid a valid imgfile")
    pass

def getCardNum(img, kenalRect):
    """
    识别并提取身份证号码
    :return:
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thr = bz.myThreshold().getMinimumThreshold(gray)
    ret, binary = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)

    # 3. 膨胀和腐蚀操作的核函数
    kenal = cv2.getStructuringElement(cv2.MORPH_RECT, (kenalRect[0], kenalRect[1]))

    dilation = cv2.dilate(binary, kenal, iterations=1)
    erosion = cv2.erode(dilation, kenal, iterations=1)

    #OCR识别
    cardNum = func.ocr(erosion)
    cardNum = func.is_identi_number(cardNum)
    if cardNum:
        return cardNum

    return False

def getChineseChar(img, kenalRect):
    """
    分析汉字区域，并识别提取
    :return:
    """
    global CARD_NAME
    global CARD_SEX
    global CARD_ETHNIC
    global CARD_YEAR
    global CARD_MON
    global CARD_DAY
    global CARD_ADDR
    global CARD_NUM

    CARD_NAME = CARD_SEX = CARD_ETHNIC = CARD_YEAR = CARD_MON = CARD_DAY = CARD_ADDR = ''

    # 图片大小比例缩小处理，为了加快性能
    h, w, _ = img.shape
    min_w = 200
    scale = 1 #min(1., w * 1. / min_w)
    h_proc = int(h * 1. / scale)
    w_proc = int(w * 1. / scale)
    im_dis = cv2.resize(img, (w_proc, h_proc))

    #灰度处理
    gray = cv2.cvtColor(im_dis, cv2.COLOR_BGR2GRAY)

    # 2. 形态学变换的预处理，得到可以查找矩形的图片

    mybz = bz.myThreshold()
    algos = mybz.getAlgos()

    for i in algos:
        #获取阈值
        thr = getattr(mybz, algos[i])(gray)
        #thr = mybz.getMinimumThreshold(gray)
        #func.showImg(gray, 'gray')

        # 膨胀和腐蚀
        ret, binary = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)

        #获取行起始坐标
        boundaryCoors = func.horizontalProjection(binary)
        if not boundaryCoors:
            continue

        #垂直投影对行内字符进行切割
        erosion = cb = copy.copy(binary)
        #func.showImg(binary, 'binary')

        coors = {} #信息所对应的坐标
        textLine = 0 #有效文本行序号
        for LineNum, boundaryCoor in enumerate(boundaryCoors):
            if textLine  == 2:
                kenal1 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
                kenal2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

                dilation = cv2.dilate(cb, kenal1, iterations=1)
                erosion = cv2.erode(dilation, kenal2, iterations=1)

            vertiCoors, text = func.verticalProjection(erosion, boundaryCoor, textLine, img)
            if len(vertiCoors) == 0:
                continue

            if textLine == 0:
                CARD_NAME = text
            elif textLine == 1:
                if text[0] != '男' and text[0] != '女':
                    CARD_SEX = func.getSexByCardNum(CARD_NUM)
                else:
                    CARD_SEX = text[0]

                CARD_ETHNIC = text[1]
            elif textLine == 2:
                #为了获取更加精准的值，通过身份证号码规则直接取得出生年月
                # CARD_YEAR = text[0]
                # CARD_MON = text[1]
                # CARD_DAY = text[2]
                pass
            else:
                CARD_ADDR += text

            if DEBUG:
                fator = 2
                for verticoo in vertiCoors:
                    box = [[verticoo[0] * scale - fator, boundaryCoor[0] * scale - fator],
                           [verticoo[1] * scale + fator, boundaryCoor[0] * scale - fator],
                           [verticoo[1] * scale + fator, boundaryCoor[1] * scale + fator],
                           [verticoo[0] * scale - fator, boundaryCoor[1] * scale + fator],
                           ]
                    cv2.drawContours(img, [np.int0(box)], 0, (0, 255, 0), 2)

            textLine += 1

        return

    return False

def findChineseCharArea(cardNumPoint1, width, hight):
    """
    根据身份证号码的位置推断姓名、性别、名族、出生年月、住址的位置
    :param cardNumPoint1: tuple 身份证号码所处的矩形的左上角坐标
    :param width: int 身份证号码所处的矩形的宽
    :param hight: int 身份证号码所处的矩形的高
    :return:
    """
    #new_x = int(cardNumPoint1[0] - (width / 18) * 6)
    new_x = cardNumPoint1[0] - (width / 18) * 5.5
    new_width = int(width/5 * 4)

    box = []
    #new_y = cardNumPoint1[1] - hight * 6.5
    card_hight = hight / (0.9044 - 0.7976)   #身份证高度
    card_y_start = cardNumPoint1[1] - card_hight * 0.7976 #粗略算出图像中身份证上边界的y坐标

    #为了保证不丢失文字区域，姓名的相对位置保留，以身份证上边界作为起始切割点
    #new_y = card_y_start# + card_hight * 0.0967

    #容错因子，防止矩形存在倾斜导致区域重叠
    factor = 20

    new_y = card_y_start if card_y_start > factor else factor

    new_hight = card_hight * (0.7616 - 0.0967) + card_hight * 0.0967

    #文字下边界坐标
    new_y_low = (new_y + new_hight) if (new_y + new_hight) <= cardNumPoint1[1] - factor else cardNumPoint1[1] - factor

    box.append([new_x, new_y])
    box.append([new_x + new_width, new_y])
    box.append([new_x + new_width, new_y_low])
    box.append([new_x, new_y_low])

    box = np.int0(box)
    return box

def detect(img):

    global CARD_NUM

    CARD_NUM = ''

    notFound = True

    # 1.  转化成灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 遍历二值化阈值算法
    algos = bz.myThreshold().getAlgos()

    for i in algos:

        #形态学变换的预处理，得到可以查找矩形的图片
        dilation = preprocess(gray, algos[i])

        # 3. 查找和筛选文字区域
        region = findTextRegion(dilation)

        # 4. 用绿线画出这些找到的轮廓
        angle = 0
        for rect in region:

            angle = rect[2]

            #识别身份证号码
            a, b = rect[1]
            if a > b:
                width = a
                hight = b
                pts2 = np.float32([[0, hight], [0, 0], [width, 0], [width, hight]])
            else:
                width = b
                hight = a
                angle = 90 + angle
                pts2 = np.float32([[width, hight], [0, hight], [0, 0], [width, 0]])

            #透视变换
            box = cv2.cv.BoxPoints(rect)
            pts1 = np.float32(box)
            M = cv2.getPerspectiveTransform(pts1, pts2)
            cropImg = cv2.warpPerspective(img, M, (int(width), int(hight)))

            # 计算核大小
            kenalx = kenaly = int(math.ceil((hight / 100.0)))
            CARD_NUM = getCardNum(cropImg, (kenalx, kenaly))
            if CARD_NUM:
                notFound = False
                #找到身份证号码，然后根据号码区域的倾斜角度，对原图进行旋转变换

                if abs(angle) > 10:
                    sp = img.shape
                    H = sp[0]
                    W = sp[1]
                    M = cv2.getRotationMatrix2D((W/2, H/2), angle, 1)
                    cropImg = cv2.warpAffine(img, M, (W, H))
                    # cv2.namedWindow("倾斜矫正", cv2.WINDOW_NORMAL)
                    # cv2.imshow("倾斜矫正", cropImg)
                    # cv2.waitKey(0)
                    #矫正图片地址
                    global curpath
                    path = 'tilt_correction.jpg'
                    newFile = os.path.join(curpath, path)
                    cv2.imwrite(newFile, cropImg)

                    return True, '', newFile

                # 画图
                if DEBUG:
                    cv2.drawContours(img, [np.int0(box)], 0, (0, 255, 0), 3)

                # 寻找汉字区域
                # 裁剪后的图片
                box = cv2.cv.BoxPoints(rect)
                box = np.int0(box)
                cropImg, point, width, hight = func.cropImgByBox(img, box)
                box = findChineseCharArea(point, width, hight)
                #cv2.drawContours(img, [box], 0, (0, 255, 0), 3)

                chiCharArea, point, width, hight = func.cropImgByBox(img, box)
                getChineseChar(chiCharArea, (kenalx, kenaly))

                # winname = "身份证号码： %s" % (CARD_NUM)
                # cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
                # cv2.imshow(winname, cropImg)
                # cv2.waitKey(0)

                break

        if notFound:
            continue
        else:
            break

    if notFound:
        #win32api.MessageBox(0, "无法识别，请换一个分辨率高点的照片~", "错误提示")
        return False, '无法识别，请换一个分辨率高点的照片~", "错误提示', ''


    # 带轮廓的图片
    if DEBUG:
        cv2.namedWindow("img", cv2.WINDOW_NORMAL)
        cv2.imshow("img", img)
        key = cv2.waitKey(0)

        cv2.destroyAllWindows()
        if key != 32:
            sys.exit()

    if CARD_NUM != '':
        # 为了获取更加精准的值，通过身份证号码规则直接取得出生年月
        CARD_YEAR, CARD_MON, CARD_DAY = func.getBirthByCardNum(CARD_NUM)

        info = """
            姓名：%s
            性别：%s     民族：%s
            出生：%s 年 %s  月 %s 日
            住址：%s
            公民身份号码：%s
        """ % (CARD_NAME, CARD_SEX, CARD_ETHNIC, CARD_YEAR, CARD_MON, CARD_DAY, CARD_ADDR, CARD_NUM)

        ret = [CARD_NAME, CARD_SEX, CARD_ETHNIC, CARD_YEAR, CARD_MON, CARD_DAY, CARD_ADDR, CARD_NUM]

        if DEBUG:
            print info

        return True, ret, ''
    else:
        return True, '', ''


def calculateElement(img):
    #根据图片大小粗略计算腐蚀 或膨胀所需核的大小
    sp = img.shape
    width = sp[1]  # width(colums) of image
    kenaly = math.ceil((width / 400.0) * 12)
    kenalx = math.ceil((kenaly / 5.0) * 4)
    a = (int(kenalx), int(kenaly))

    return a

def preprocess(gray, algoFunc):
    # 1. Sobel算子，x方向求梯度
    #sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize = 3)

    #获取二值化阈值
    thr = bz.myThreshold()
    #threshold = thr.get1DMaxEntropyThreshold(gray)
    threshold = getattr(thr, algoFunc)(gray)
    if threshold <= 0:
        raise Exception("获取二值化阈值失败")

    # 2. 二值化
    ret, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    #获取核大小
    calculateElement(gray)

    # 3. 膨胀和腐蚀操作的核函数
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, calculateElement(gray))

    #微处理去掉小的噪点
    dilation = cv2.dilate(binary, element1, iterations=1)
    binary = cv2.erode(dilation, element1, iterations=1)

    #文字膨胀与腐蚀使其连成一个整体
    erosion = cv2.erode(binary, element2, iterations=1)
    dilation = cv2.dilate(erosion, element1, iterations=1)

    # 7. 存储中间图片
    # cv2.namedWindow("binary", cv2.WINDOW_NORMAL)
    # cv2.imshow("binary", binary)
    # cv2.waitKey(0)
    #
    # cv2.namedWindow("dilation2", cv2.WINDOW_NORMAL)
    # cv2.imshow("dilation2", erosion)
    # cv2.waitKey(0)
    #
    # cv2.namedWindow("dilation2", cv2.WINDOW_NORMAL)
    # cv2.imshow("dilation2", dilation)
    # cv2.waitKey(0)

    cv2.destroyAllWindows()
    #sys.exit(0)



    return dilation


def findTextRegion(img):
    region = []

    # 1. 查找轮廓
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 2. 筛选那些面积小的
    for i in range(len(contours)):
        cnt = contours[i]
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)
        # 面积小的都筛选掉
        if(area < 1000):
            continue

        # 找到最小的矩形，该矩形可能有方向
        rect = cv2.minAreaRect(cnt)

        # 计算高和宽 参考：http://blog.csdn.net/lanyuelvyun/article/details/76614872
        width = rect[1][0]
        hight = rect[1][1]

        # 筛选那些太细的矩形，留下扁的
        if hight > width:
            if hight < width * 5:
                continue
        else:
            if width < hight * 5:
                continue

        region.append(rect)

    return region


def nothing(x):
    pass


def fushiyupengzhang(pathtoimage):
    """
    腐蚀与膨胀动态取值预览
    :param pathtoimage:
    :return:
    """
    img = cv2.imread(pathtoimage)
    im_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #sobel = cv2.Sobel(im_gray, cv2.CV_8U, 1, 0, ksize=3)

    # 获取二值化阈值
    thr = bz.myThreshold()
    threshold = thr.getMinimumThreshold(im_gray)
    if threshold <= 0:
        raise Exception("获取二值化阈值失败")
    retval, img = cv2.threshold(im_gray, threshold, 255, cv2.THRESH_BINARY)

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.imshow('image', img)
    cv2.createTrackbar('Er/Di', 'image', 0, 1, nothing)
    # 创建腐蚀或膨胀选择滚动条，只有两个值
    cv2.createTrackbar('x', 'image', 0, 100, nothing)
    # 创建卷积核大小滚动条

    cv2.createTrackbar('y', 'image', 0, 100, nothing)

    while (1):
        s = cv2.getTrackbarPos('Er/Di', 'image')
        x = cv2.getTrackbarPos('x', 'image')
        y = cv2.getTrackbarPos('y', 'image')
        # 分别接收两个滚动条的数据

        if x == 0:
            x = 1
        if y == 0:
            y = 1

        k = cv2.waitKey(1)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (x, y))
        # 根据滚动条数据确定卷积核大小
        erroding = cv2.erode(img, kernel, iterations=1)
        dilation = cv2.dilate(img, kernel, iterations=1)
        if k == 27:
            break
            # esc键退出
        if s == 0:
            cv2.imshow('image', erroding)
        else:
            cv2.imshow('image', dilation)
            # 判断是腐蚀还是膨胀


def  imgRotation(pathtoimg):
    #图片自动旋正
    from PIL import Image
    img = Image.open(pathtoimg)

    if hasattr(img, '_getexif') and img._getexif() != None:
        # 获取exif信息
        dict_exif = img._getexif()
        if dict_exif.has_key(274):
            if dict_exif[274] == 3:
                #顺时针180
                new_img = img.rotate(-180)
                new_img.save(pathtoimg)
            elif dict_exif[274] == 6:
                #顺时针90°
                new_img = img.rotate(-90)
                new_img.save(pathtoimg)
            elif dict_exif[274] == 8:
                #逆时针90°
                new_img = img.rotate(90)
                new_img.save(pathtoimg)


    return None


def enhanceImage(pathtoimg):
    from PIL import Image
    from PIL import ImageEnhance

    # 原始图像
    image = Image.open(pathtoimg)

    # 对比度增强
    enh_con = ImageEnhance.Contrast(image)
    contrast = 1.5
    image_contrasted = enh_con.enhance(contrast)
    image_contrasted.show()

if __name__ == '__main__':

    # for i in range(31, 40):
    #     pathtoimg = r'D:\OCR\p\w%s.jpg' % (i)
    #     #pathtoimg = r'D:\OCR\p\sam_xie.jpg'

    if DEBUG:
        pathtoimg = r'images\w1.jpg'

    # 读取文件
    img = cv2.imread(pathtoimg)

    try:
        ret, msg, path = detect(img)
        if path != '':
            # 读取文件
            img = cv2.imread(path)

            ret, msg, _ = detect(img)
            os.unlink(path)
            if ret:
                result = [{i: msg[i]} for i in range(len(msg))]
                print json.dumps(result)
            else:
                print msg

        else:
            if ret:
                result = [{i: msg[i]} for i in range(len(msg))]
                print json.dumps(result)
            else:
                print msg
    except Exception, e:
        print e

    #fushiyupengzhang(pathtoimg)