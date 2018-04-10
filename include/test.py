# -*- coding: utf-8 -*-

import sys
import os
import uuid
import subprocess
import codecs



TESSERACT_OCR = "/usr/local/bin/tesseract"

curpath = ''
if getattr(sys, 'frozen', False):
    curpath = os.path.dirname(sys.executable)
elif __file__:
    curpath = os.path.dirname(os.path.realpath(__file__))

filename = uuid.uuid4().__str__() + '.jpg'
txt = uuid.uuid4().__str__()

unique_filename = 'e507900b-c3ae-4c37-bffb-a399e7fc511c.jpg'
unique_txt = curpath + '/' + txt
print unique_txt

psm = 7
lang = 'eng'

subprocess.call([TESSERACT_OCR, unique_filename, unique_txt, '-l', lang, '-psm', psm], shell=True)

txtfile = unique_txt + '.txt'
fp = os.open(txtfile, os.O_RDONLY)
text = os.read(fp, 1024)
os.close(fp)

if text[:3] == codecs.BOM_UTF8:
    text = text[3:]

os.unlink(unique_filename)
os.unlink(txtfile)

