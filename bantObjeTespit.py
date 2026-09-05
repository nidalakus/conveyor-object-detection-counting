import cv2 as cv
import numpy as np 
import os

altyesil = np.array([26, 27, 35])
ustyesil = np.array([121, 200, 251])

def bant_maskesi_bul(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    yesil_mask = cv.inRange(hsv, altyesil, ustyesil)

    kernel = np.ones((7,7), np.uint8)
    yesil_mask = cv.morphologyEx(yesil_mask, cv.MORPH_CLOSE, kernel)
    yesil_mask = cv.morphologyEx(yesil_mask, cv.MORPH_OPEN, kernel)

    contours, hierarchy = cv.findContours(yesil_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, None

    en_buyuk = max(contours, key=cv.contourArea)
    if cv.contourArea(en_buyuk) < 5000:
        return None, None, None

    x, y, w, h = cv.boundingRect(en_buyuk)
    bant_sekli_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv.drawContours(bant_sekli_mask, [en_buyuk], -1, 255, thickness=cv.FILLED)
    return (x, y, w, h), bant_sekli_mask, yesil_mask


def objeleri_bul(frame, bant_box, bant_sekli_mask):
    x, y, w, h = bant_box
    roi = frame[y:y+h, x:x+w]
    sekil_roi = bant_sekli_mask[y:y+h, x:x+w]

    hsv_roi = cv.cvtColor(roi, cv.COLOR_BGR2HSV)
    mask_roi = cv.inRange(hsv_roi, altyesil, ustyesil)

    obje_mask = cv.bitwise_not(mask_roi)
    obje_mask = cv.bitwise_and(obje_mask, sekil_roi)

    kernel = np.ones((7,7), np.uint8)
    obje_mask = cv.morphologyEx(obje_mask, cv.MORPH_OPEN, kernel)
    obje_mask = cv.morphologyEx(obje_mask, cv.MORPH_CLOSE, kernel)

    contours, hierarchy = cv.findContours(obje_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return contours, (x,y)

def solidity_hesapla(contours):
    alan = cv.contourArea(contours)
    hull = cv.convexHull(contours)
    hull_alani = cv.contourArea(hull)
    if hull_alani == 0:
        return 0
    return alan / hull_alani

def despill_yap(bgr, mask):
    bgr = bgr.astype(np.float32)
    b, g, r = cv.split(bgr)

    ortalama_rb = (r + b) / 2.0
    fazla_yesil = np.maximum(g - ortalama_rb, 0)
    g_temiz = g - fazla_yesil * 0.8

    bgr_temiz = cv.merge([b, g_temiz, r]).clip(0, 255).astype(np.uint8)
    b2, g2, r2 = cv.split(bgr_temiz)
    bgra = cv.merge([b2, g2, r2, mask])
    return bgra

def merkez_bul(x, y, w, h):
    return (x + w // 2, y + h // 2)


def mesafe(nokta1, nokta2):
    return np.sqrt((nokta1[0] - nokta2[0]) ** 2 + (nokta1[1] - nokta2[1]) ** 2)


def takibi_guncelle(takip_edilenler, anlik_merkezler, sonraki_id, esik_mesafe=60, onay_esik=3, kayip_esik=5):
    kullanilan_id = set()
    yeni_sayilan = 0
    eslesen_idler = []

    for merkez in anlik_merkezler:
        en_yakin_id = None
        en_yakin_mesafe = esik_mesafe

        for obj_id, bilgi in takip_edilenler.items():
            if obj_id in kullanilan_id:
                continue
            d = mesafe(merkez, bilgi['merkez'])
            if d < en_yakin_mesafe:
                en_yakin_mesafe = d
                en_yakin_id = obj_id

        if en_yakin_id is not None:
            takip_edilenler[en_yakin_id]['merkez'] = merkez
            takip_edilenler[en_yakin_id]['gorulme'] += 1
            takip_edilenler[en_yakin_id]['kayip'] = 0
            kullanilan_id.add(en_yakin_id)
            eslesen_idler.append(en_yakin_id)
        else:
            takip_edilenler[sonraki_id] = {
                'merkez': merkez, 'gorulme': 1, 'kayip': 0, 'sayildi': False
            }
            kullanilan_id.add(sonraki_id)
            eslesen_idler.append(sonraki_id)
            sonraki_id += 1

    for obj_id in list(takip_edilenler.keys()):
        if obj_id not in kullanilan_id:
            takip_edilenler[obj_id]['kayip'] += 1

    yeni_sayilan_idler = []  # <-- bu karede onaylanan id'ler
    for obj_id, bilgi in takip_edilenler.items():
        if bilgi['gorulme'] >= onay_esik and not bilgi['sayildi']:
            bilgi['sayildi'] = True
            yeni_sayilan += 1
            yeni_sayilan_idler.append(obj_id)

    for obj_id in list(takip_edilenler.keys()):
        if takip_edilenler[obj_id]['kayip'] > kayip_esik:
            del takip_edilenler[obj_id]

    return takip_edilenler, sonraki_id, yeni_sayilan, eslesen_idler, yeni_sayilan_idler

def sticker_kaydet(frame, c, ofset_x, ofset_y, sayac, klasor="kaydedilen_objeler"):
    if not os.path.exists(klasor):
        os.makedirs(klasor)
        
    x, y, w, h = cv.boundingRect(c)
    gercek_x = x + ofset_x
    gercek_y = y + ofset_y
    h_frame, w_frame = frame.shape[:2]
    
    x1, y1 = max(0, gercek_x), max(0, gercek_y)
    x2, y2 = min(w_frame, gercek_x + w), min(h_frame, gercek_y + h)
    
    sticker_bgr = frame[y1:y2, x1:x2]
    
    if sticker_bgr.size == 0:
        return
    
    mask = np.zeros((h, w), dtype=np.uint8)
    local_c = c.copy()
    local_c[:, 0, 0] -= x  # x kaydırması
    local_c[:, 0, 1] -= y  # y kaydırması
        
    cv.drawContours(mask, [local_c], -1, (255), thickness=cv.FILLED)

    erode_kernel = np.ones((3,3), np.uint8)
    mask = cv.erode(mask, erode_kernel, iterations=2)
    mask = cv.GaussianBlur(mask, (3,3), 0)
    
    kirpma_x = x1 - gercek_x
    kirpma_y = y1 - gercek_y
    mask_cropped = mask[kirpma_y:kirpma_y + sticker_bgr.shape[0],
                        kirpma_x:kirpma_x + sticker_bgr.shape[1]]
        
    sticker_bgra = despill_yap(sticker_bgr, mask_cropped)
    
    dosya_yolu = os.path.join(klasor, f"frame{sayac:05d}.png")
    cv.imwrite(dosya_yolu, sticker_bgra)

def baslangic_sayaci_bul(klasor="kaydedilen_objeler"):
    if not os.path.exists(klasor):
        return 0

    en_buyuk = -1

    for dosya_adi in os.listdir(klasor):
        if dosya_adi.startswith("frame") and dosya_adi.endswith(".png"):
            sayi_metni = dosya_adi[len("frame"):-len(".png")]

            if sayi_metni.isdigit():
                numara = int(sayi_metni)
                en_buyuk = max(en_buyuk, numara)

    return en_buyuk + 1