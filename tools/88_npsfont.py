# -*- coding: utf-8 -*-
# NPS 소형 명판 폰트 변형 비교 (볼드/크기)
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from PIL import Image, ImageFont, ImageDraw

WORK = r'C:\Emul\Switch\패치유틸.xdeltaUI\work'

def mask_img(s, px, bold, thr):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    d = ImageDraw.Draw(img)
    d.text((4, 4), s, fill=255, font=font)
    if bold:
        d.text((5, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    return img.crop(img.getbbox())

sheet = Image.new('L', (460, 140), 30)
dr = ImageDraw.Draw(sheet)
y = 14
for s in ('유봉', '포신', '하후연'):
    x = 4
    for bold in (True, False):
        for px in (10, 11):
            m = mask_img(s, px, bold, 110)
            sheet.paste(m, (x, y))
            dr.text((x, y-12), f'{"B" if bold else "N"}{px}', fill=200)
            x += m.width + 14
    y += 42
sheet = sheet.resize((sheet.width*3, sheet.height*3), Image.NEAREST)
sheet.save(os.path.join(WORK, 'nps_font_test.png'))
print('ok')
