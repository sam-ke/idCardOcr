# -*- coding: utf-8 -*-
import cv2
import sys
import math
import numpy as np
import os
import uuid
import subprocess
import codecs
import platform

def is_number(s):
    """
    检查字符串是否为数字
    :param s:
    :return:
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def is_identi_number(num):
    """
    检查是否为省份证号码
    :param num:
    :return:
    """
    #print "card num:", num
    chars = [chr(i) for i in range(88, 123)]
    num = str(num).strip()

    newNum = ''
    for i in num:
        if i in chars or is_number(i):
            newNum += i

    strlen = len(newNum)
    if strlen == 18 or strlen == 15:
        return newNum
    else:
        return  False

def cropImgByBox(imgSrc, box):
    """
    通过顶点矩阵，裁剪图片
    :param imgSrc:
    :param box:
    :return:
    """

    Xs = [i[0] for i in box]
    Ys = [i[1] for i in box]
    x1 = min(Xs)
    x2 = max(Xs)
    y1 = min(Ys)
    y2 = max(Ys)
    hight = y2 - y1
    width = x2 - x1
    # 裁剪
    cropImg = imgSrc[y1:y1 + hight, x1:x1 + width]

    return cropImg, (x1, y1), width, hight


def ishan(text):
    # for python 2.x, 3.3+
    # sample: ishan(u'一') == True, ishan(u'我&&你') == False
    return all(u'\u4e00' <= char <= u'\u9fff' for char in text)

def delSpaceLine(text):
    """
    删除文本的空行
    :param text:
    :return:
    """
    texts = text.split("\n")
    newTextArr = []
    for line in texts:
        data = line.strip()
        if len(data) != 0:
            newTextArr.append(line)

    return "\n".join(str(i) for i in newTextArr)

def iconv(code,newcode,str):
    try:
        out=unicode(str,code,'ignore')
        outgbk=out.encode(newcode,'ignore')
        return outgbk
    except:
        return str

def showImg(img, winName='img'):
    cv2.namedWindow(winName, cv2.WINDOW_NORMAL)
    cv2.imshow(winName, img)
    cv2.waitKey(0)
    return


def horizontalProjection(BinaryImg):
    """
    水平投影边界坐标
    :return:
    """
    #水平行边界坐标
    boundaryCoors = []
    (x, y) = BinaryImg.shape
    a = [0 for z in range(0, x)]

    for i in range(0, x):
        for j in range(0, y):
            if BinaryImg[i, j] == 0:
                a[i] = a[i] + 1
                #BinaryImg[i, j] = 255  # to be white

    #连续区域标识
    continuouStartFlag = False
    up = down = 0
    tempUp = 0  #行高不足总高1/20,临时保存，考虑与下一个行合并。主要解决汉字中上下结构的单子行像素点不连续的问题

    for i in range(0, x):
        # for j in range(0, a[i]):
        #     BinaryImg[i, j] = 0

        if a[i] > 1 :
            if not continuouStartFlag:
                continuouStartFlag = True
                up = i
        else:
            if continuouStartFlag:
                continuouStartFlag = False
                down = i - 1
                if down - up >= x / 20 and down -up <= x/10:
                    #行高小于总高1/20的抛弃
                    boundaryCoors.append([up, down])
                else:
                    if tempUp > 0:
                        if down - tempUp >= x / 20 and down - tempUp <= x/10:
                            # 行高小于总高1/20的抛弃
                            boundaryCoors.append([tempUp, down])
                            tempUp = 0
                    else:
                        tempUp = up

    #print boundaryCoors
    #showImg(BinaryImg, 'BinaryImg')
    if len(boundaryCoors) < 4:
        return False

    return boundaryCoors

def verticalProjection(BinaryImg, horiBoundaryCoor, LineNum, orginImg=None):
    """
    垂直投影对行内字符进行切割
    :param BinaryImg:   二值化图像
    :param boundaryCoors:  #行起始坐标
    :param LineNum:  #行序号 0：姓名  1：性别 名族  2：生日 >=3：住址
    :return:
    """
    LineNum = 3 if LineNum >= 3 else LineNum

    switch={
        0: CardName,
        1: CardSexAndEthic,
        2: CardBirth,
        3: CardAddress,
    }

    return switch[LineNum](BinaryImg, horiBoundaryCoor, orginImg)

def CardCharCommonDeal(BinaryImg, horiBoundaryCoor):
    """
    文字通用切割处理
    :param BinaryImg:
    :param horiBoundaryCoor:
    :return:
    """
    # 列边界坐标
    vertiBoundaryCoors = []

    up, down = horiBoundaryCoor
    lineHight = down - up

    (x, y) = BinaryImg.shape
    a = [0 for z in range(0, y)]

    for j in range(0, y):
        for i in range(up, down):
            if BinaryImg[i, j] == 0:
                a[j] = a[j] + 1
                #BinaryImg[i, j] = 255  # to be white

    # 连续区域标识
    continuouStartFlag = False
    left = right = 0

    pixelNum = 0  # 统计每个列的像素数量
    maxWidth = 0  #最宽的字符长度
    for i in range(0, y):
        # for i in range((down - a[j]), down):
        #     BinaryImg[i, j] = 0
        pixelNum += a[i]  # 统计像素
        if a[i] > 0:
            if not continuouStartFlag:
                continuouStartFlag = True
                left = i
        else:
            if continuouStartFlag:
                continuouStartFlag = False
                right = i
                if right - left > 0:
                    if pixelNum > lineHight * (right - left) / 10:
                        curW = right - left
                        maxWidth = curW if curW > maxWidth else maxWidth
                        vertiBoundaryCoors.append([left, right])
                    pixelNum = 0  # 遇到边界，归零

    #showImg(BinaryImg, 'BinaryImgBinaryImg')
    return vertiBoundaryCoors, maxWidth


def _chineseCharHandle(BinaryImg, horiBoundaryCoor):
    fator = 0.9

    vertiBoundaryCoors, maxWidth = CardCharCommonDeal(BinaryImg, horiBoundaryCoor)
    newVertiBoundaryCoors = []  # 字符合并后的垂直系列坐标

    charNum = len(vertiBoundaryCoors)

    i = 0
    while i < charNum:
        if i + 1 >= charNum:
            newVertiBoundaryCoors.append(vertiBoundaryCoors[i])
            break

        curCharWidth = vertiBoundaryCoors[i][1] - vertiBoundaryCoors[i][0]
        if curCharWidth < maxWidth * fator:
            if vertiBoundaryCoors[i + 1][1] - vertiBoundaryCoors[i][0] <= maxWidth*(2 - fator):
                newVertiBoundaryCoors.append([vertiBoundaryCoors[i][0], vertiBoundaryCoors[i + 1][1]])
                i += 1
            elif curCharWidth > maxWidth / 4:
                newVertiBoundaryCoors.append(vertiBoundaryCoors[i])
        else:
            newVertiBoundaryCoors.append(vertiBoundaryCoors[i])

        i += 1
    return newVertiBoundaryCoors


def CardName(BinaryImg, horiBoundaryCoor, origin=None):
    """
    身份证姓名
    :param BinaryImg:
    :param horiBoundaryCoor:
    :param origin:
    :return:coors, text
    """


    coors = _chineseCharHandle(BinaryImg, horiBoundaryCoor)
    if len((coors)) == 0:
        return coors, ''

    up, down = horiBoundaryCoor

    box = np.int0([[coors[0][0], up], [coors[-1][1], up], [coors[-1][1], down], [coors[0][0], down]])

    text = ''
    if type(origin) == np.ndarray:
        cropImg, _, _, _ = cropImgByBox(origin, box)
        text = ocr(cropImg, 'chi_sim', '7')

    return coors, text.replace(' ', '')


def CardSexAndEthic(BinaryImg, horiBoundaryCoor, origin=None):
    """
    身份证性别 名族
    :param BinaryImg:
    :param horiBoundaryCoor:
    :param origin:
    :return:
    """
    text = ['', '']

    coors = _chineseCharHandle(BinaryImg, horiBoundaryCoor)
    up, down = horiBoundaryCoor

    maxW = 0
    for coo in coors:
        curW = coo[1] - coo[0]
        maxW = curW if curW > maxW else maxW

    textIndex = 0
    if type(origin) == np.ndarray:
        for i in range(len(coors)):
            box = np.int0([[coors[i][0], up], [coors[i][1], up], [coors[i][1], down], [coors[i][0], down]])
            if (coors[i][1] - coors[i][0]) < maxW * 0.88:
                continue

            cropImg, _, _, _ = cropImgByBox(origin, box)
            char = ocr(cropImg, 'chi_sim', '6')
            if textIndex == 0:
                text[0] = char  #性别
            else:
                if char == '民' or char == '族':
                    continue
                elif char == '又' or char == '汊':
                    text[1] += '汉'
                elif ishan(char.decode('utf8')):
                    text[1] += char

            textIndex += 1

    #默认为汉族
    if len(text[1]) == 0:
        text[1] = '汉'

    return coors, text

def getBirthByCardNum(cardnum):
    """
    通过身份证号码规则直接获取出身年月
    :param cardnum:
    :return:
    """
    texts = []

    if len(cardnum) == 18:
        texts.append(cardnum[6:10])

        if cardnum[10] != '0':
            texts.append(cardnum[10:12])
        else:
            texts.append(cardnum[11])

        if cardnum[12] != '0':
            texts.append(cardnum[12:14])
        else:
            texts.append(cardnum[13])
    else:
        texts.append('19'+str(cardnum[6:8]))
        if cardnum[8] != 0:
            texts.append(cardnum[8:10])
        else:
            texts.append(cardnum[9])
        if cardnum[10] != 0:
            texts.append(cardnum[10:12])
        else:
            texts.append(cardnum[11])

    return texts

def CardBirth(BinaryImg, horiBoundaryCoor, origin=None):
    """
    身份证出生
    :param BinaryImg:
    :param horiBoundaryCoor:
    :return:
    """
    up, down = horiBoundaryCoor
    lineHight = down - up  # 字符高度

    vertiBoundaryCoors, maxWidth = CardCharCommonDeal(BinaryImg, horiBoundaryCoor)
    newVertiBoundaryCoors = []  # 字符合并后的垂直系列坐标




    i = 0
    charNum = len(vertiBoundaryCoors)

    Section = [[] for j in range(charNum)]  # 按距离把字符分段
    sectIndex = 0

    while i < charNum:
        #当前字符宽度
        # curCharWidth = vertiBoundaryCoors[i][1] - vertiBoundaryCoors[i][0]
        if i+1 < charNum:
            rightDis = vertiBoundaryCoors[i+1][0] - vertiBoundaryCoors[i][1]
            if rightDis < 10:
                Section[sectIndex].append(vertiBoundaryCoors[i])
            else:
                Section[sectIndex].append(vertiBoundaryCoors[i])
                sectIndex += 1
        else:
            Section[sectIndex].append(vertiBoundaryCoors[i])

        i += 1

    retSection = []
    for i in range(len(Section)):
        if len(Section[i]) > 0:
            retSection.append(Section[i])

    # print vertiBoundaryCoors
    # print Section
    # print retSection

    YearCoor, index = _getYear(retSection, lineHight)
    yearLenght = YearCoor[1] - YearCoor[0]
    newVertiBoundaryCoors.append(YearCoor)

    month, index = _getMonth(retSection, index, yearLenght)
    if month:
        newVertiBoundaryCoors.append(month)

    DayCoor, index = _getDay(retSection, index, yearLenght)
    if DayCoor:
        newVertiBoundaryCoors.append(DayCoor)

    text = ['', '', '']

    # 减少ocr的调用，挺高性能， 只保留位置提取
    # if type(origin) == np.ndarray:
    #     for i in range(len(newVertiBoundaryCoors)):
    #         box = np.int0([[newVertiBoundaryCoors[i][0], up],
    #                        [newVertiBoundaryCoors[i][1], up],
    #                        [newVertiBoundaryCoors[i][1], down],
    #                        [newVertiBoundaryCoors[i][0], down]])
    #
    #         cropImg, _, _, _ = cropImgByBox(origin, box)
    #         chars = ocr(cropImg, 'eng', '7')
    #         text[i] = str(filterNonnumericChar(chars))
    return newVertiBoundaryCoors, text

def _getYear(Section, lineHight):
    _len = len(Section[0])
    if _len == 4:
        return [Section[0][0][0], Section[0][-1][1]], 0
    elif _len < 4:
        if Section[0][-1][1] - Section[0][0][0] > lineHight*3/2:
            return [Section[0][0][0], Section[0][-1][1]], 0
        else:
            _lenS = len(Section)
            for i in range(1, _lenS):
                if Section[i][-1][1] - Section[0][0][0] > lineHight * 2:
                    return [Section[0][0][0], Section[i][-1][1]], i
    else:
        return [Section[0][0][0], Section[0][-1][1]], 0

def _getMonth(Section, index, yearLenght):
    _lenS = len(Section)

    StartIndex = index + 1
    if StartIndex < _lenS:
        for i in range(StartIndex, _lenS):
            if Section[i][0][0] - Section[index][-1][1] < yearLenght *2/3:
                _leni = len(Section[i])
                if _leni > 1:
                    for j in range(1, _leni):
                        if Section[i][j][0] - Section[index][-1][1] > yearLenght *2/3:
                            _w = 0
                            for k in range(j, _leni):
                                _w += Section[i][k][1] - Section[i][k][0]
                                if _w < yearLenght/2:
                                    continue
                                else:
                                    if _w > yearLenght * 0.6:
                                        return [Section[i][j][0], Section[i][k-1][1]], i
                                    else:
                                        return [Section[i][j][0], Section[i][k][1]], i
                            return [Section[i][j][0], Section[i][-1][1]], i
                else:
                    continue
            else:
                if Section[i][-1][0] - Section[i][0][0] < yearLenght/4:
                    if i+1 < _lenS and Section[i+1][-1][1] - Section[i][0][0] <= yearLenght/2:
                        return [Section[i][0][0], Section[i+1][-1][1]], i+1
                    else:
                        return [Section[i][0][0], Section[i][-1][1]], i
                else:
                    return [Section[i][0][0], Section[i][-1][1]], i
    return False, StartIndex

def _getDay(Section, index, yearLenght):
    return _getMonth(Section, index, yearLenght)

def CardAddress(BinaryImg, horiBoundaryCoor, origin=None):
    """
    身份证地址
    :param BinaryImg:
    :param horiBoundaryCoor:
    :return:
    """

    coors = _chineseCharHandle(BinaryImg, horiBoundaryCoor)
    up, down = horiBoundaryCoor

    box = np.int0([[coors[0][0], up], [coors[-1][1], up], [coors[-1][1], down], [coors[0][0], down]])

    text = ''
    if type(origin) == np.ndarray:
        cropImg, _, _, _ = cropImgByBox(origin, box)
        text = ocr(cropImg, 'chi_sim', '7')

    return coors, text.replace(' ', '')

def ocr(imgSrc, lang=None, psm='3'):
    """
    OCR 识别
    :param imgSrc:  图片资源
    :param lang:  语言包
    :return: 识别内容
    """

    curpath = ''
    if getattr(sys, 'frozen', False):
        curpath = os.path.dirname(sys.executable)
    elif __file__:
        curpath = os.path.dirname(os.path.realpath(__file__))

    filename = uuid.uuid4().__str__() + '.jpg'
    txt = uuid.uuid4().__str__()

    unique_filename = curpath + '/' + filename
    unique_txt = curpath + '/' + txt

    cv2.imwrite(unique_filename, imgSrc)
    if lang == None:
        lang = 'eng'

    sysstr = platform.system()
    if (sysstr == "Windows"):
        TESSERACT_OCR = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        subprocess.call([TESSERACT_OCR, unique_filename, unique_txt, '-l', lang, '-psm', psm], shell=True)
    elif (sysstr == "Linux"):
        #TESSERACT_OCR = "/usr/local/bin/tesseract"
        TESSERACT_OCR = "/usr/bin/tesseract"
        if os.access(TESSERACT_OCR, os.X_OK):
            subprocess.call(TESSERACT_OCR + " "+ unique_filename + " "+  unique_txt + ' -l '+ lang +' -psm '+ str(psm), shell=True)
        else:
            raise Exception("命令%s  不存在"%(TESSERACT_OCR))

    txtfile = unique_txt + '.txt'
    fp = os.open(txtfile, os.O_RDONLY)
    text = os.read(fp, 1024)
    os.close(fp)

    if text[:3] == codecs.BOM_UTF8:
        text = text[3:]

    os.unlink(unique_filename)
    os.unlink(txtfile)

    return text.strip('\n')


def filterNonnumericChar(str):
    """
    过滤非数字字符
    :param str:
    :return:
    """
    newText = ''
    text = str.decode('utf8')
    for char in text:
        if is_number(char):
            newText += char

    return newText

def getSexByCardNum(cardNum):
    """
    根据身份证的顺序位，判断性别
    :param cardNum:
    :return:
    """
    if int(cardNum[-2]) % 2 == 0:
        return '女'
    else:
        return '男'

