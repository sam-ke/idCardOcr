# -*- coding: utf-8
import cv2
import sys
import math
 

class myThreshold:
    '''
    二值化算法大全
    '''

    def getMinimumThreshold(self, imgSrc):
        """
        谷底最小值的阈值
        """
        Y = Iter = 0
        HistGramC = []
        HistGramCC = []

        #获取直方数组
        hist_cv = self.__getHisGram(imgSrc)

        for Y in range(256):
            HistGramC.append(hist_cv[Y])
            HistGramCC.append(hist_cv[Y])

        #通过三点求均值来平滑直方图
        while( self.__IsDimodal(HistGramCC) == False):
            HistGramCC[0] = (HistGramC[0] + HistGramC[0] + HistGramC[1]) / 3.0 #第一点
            for Y in range(1, 255):
                HistGramCC[Y] = (HistGramC[Y - 1] + HistGramC[Y] + HistGramC[Y + 1]) / 3 #中间的点

            HistGramCC[255] = (HistGramC[254] + HistGramC[255] + HistGramC[255]) / 3 #最后一点
            HistGramC = HistGramCC
            Iter += 1
            if (Iter >= 1000):
                return -1

        #阈值极为两峰之间的最小值
        Peakfound = False
        for Y in range(1, 255):
            if (HistGramCC[Y - 1] < HistGramCC[Y] and HistGramCC[Y + 1] < HistGramCC[Y]):
                Peakfound = True
            if (Peakfound == True and HistGramCC[Y - 1] >= HistGramCC[Y] and HistGramCC[Y + 1] >= HistGramCC[Y]):
                return Y - 1
        return -1

    def __IsDimodal(self, HistGram):
        #对直方图的峰进行计数，只有峰数位2才为双峰
        Count = 0

        for Y in range(1, 255):
            if HistGram[Y - 1] < HistGram[Y] and HistGram[Y + 1] < HistGram[Y]:
                Count += 1
                if(Count > 2):
                    return False

        if Count == 2:
            return True
        else:
            return False

    def __getHisGram(self, imgSrc):
        hist_cv = cv2.calcHist([imgSrc], [0], None, [256], [0, 256])
        return hist_cv

    def get1DMaxEntropyThreshold(self, imgSrc):
        """
        一维最大熵
        """
        X = Y = Amount = 0
        HistGramD = {}
        MinValue = 0
        MaxValue = 255
        Threshold = 0

        HistGram = self.__getHisGram(imgSrc)

        for i in range(256):
            if HistGram[MinValue] == 0:
                MinValue += 1
            else:
                break

        while MaxValue > MinValue and HistGram[MinValue] == 0:
            MaxValue -= 1

        if (MaxValue == MinValue):
            return MaxValue     #图像中只有一个颜色
        if (MinValue + 1 == MaxValue):
            return MinValue     #图像中只有二个颜色

        for Y in range(MinValue, MaxValue + 1):
            Amount += HistGram[Y]  #像素总数

        for Y in range(MinValue, MaxValue + 1):
            HistGramD[Y] = HistGram[Y] / Amount +1e-17

        MaxEntropy = 0.0
        for Y in range(MinValue + 1, MaxValue):
            SumIntegral = 0
            for X in range(MinValue, Y + 1):
                SumIntegral += HistGramD[X]

            EntropyBack = 0
            for X in range(MinValue, Y + 1):
                EntropyBack += (- HistGramD[X] / SumIntegral * math.log(HistGramD[X] / SumIntegral))

            EntropyFore = 0
            for X in range(Y + 1, MaxValue + 1):
                SumI = 1 - SumIntegral
                if SumI < 0:
                    SumI = abs(SumI)
                elif SumI == 0:
                    continue

                EntropyFore += (- HistGramD[X] / (1 - SumIntegral) * math.log(HistGramD[X] / SumI))

            if MaxEntropy < (EntropyBack + EntropyFore):
                Threshold = Y
                MaxEntropy = EntropyBack + EntropyFore

        if Threshold > 5:
            return Threshold - 5 #存在误差
        return Threshold


    def getIsoDataThreshold(self, imgSrc):
        """
        ISODATA （intermeans） 阈值算法
        :param imgSrc:
        :return:
        """

        HistGram = self.__getHisGram(imgSrc)
        g = 0
        for i in range(1, len(HistGram)):
            if HistGram[i] > 0:
                g = i + 1
                break

        while True:
            l = 0
            totl = 0
            for i in range(0, g):
                totl = totl + HistGram[i]
                l = l + (HistGram[i] * i)

            h = 0
            toth = 0
            for i in range(g+1, len(HistGram)):
                toth += HistGram[i]
                h += (HistGram[i] * i)

            if totl > 0 and toth > 0:
                l = l/totl
                h = h/toth
                if g == int(round((l + h) / 2.0)):
                    break
            g += 1
            if g > len(HistGram) - 2:
                return 0

        return g

    def getIntermodesThreshold(self, imgSrc):

        HistGram = self.__getHisGram(imgSrc)
        return 126

    def getAlgos(self):
        """
        获取阈值算法
        :param index:
        :return:
        """

        algos = {
            0 : 'getMinimumThreshold',  #谷底最小值
            1 : 'get1DMaxEntropyThreshold', #一维最大熵
            2 : 'getIsoDataThreshold', #intermeans
            #3 : 'getKittlerMinError', #kittler 最小错误
            4 : 'getIntermodesThreshold', #双峰平均值的阈值
        }

        return algos


if __name__=='__main__':
    pass