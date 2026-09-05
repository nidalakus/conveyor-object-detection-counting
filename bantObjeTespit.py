import cv2 as cv
import numpy as np 
import os

altyesil = np.array([18, 27, 26])
ustyesil = np.array([121, 255, 255])

def en_buyuk_ikili_dikdortgen(mask, margin = 0.01):
    
    binary = (mask > 0).astype(np.int32)
    rows, cols = binary.shape

    yukseklik = np.zeros(cols, dtype=np.int32)
    en_iyi_alan = 0
    en_iyi_dikdortgen = (0, 0, 0, 0)

    for satir in range(rows):
        for sutun in range(cols):
            if binary[satir, sutun]:
                yukseklik[sutun] += 1
            else:
                yukseklik[sutun] = 0

        stack = []
        for sutun in range(cols + 1):
            h = yukseklik[sutun] if sutun < cols else 0
            baslangic = sutun

            while stack and stack[-1][1] >= h:
                idx, yuks = stack.pop()
                genislik = sutun - idx
                alan = yuks * genislik
                if alan > en_iyi_alan:
                    en_iyi_alan = alan
                    en_iyi_dikdortgen = (idx, satir - yuks + 1, genislik, yuks)
                baslangic = idx

            stack.append((baslangic, h))
    
    if en_iyi_alan == 0:
        return (0, 0, 0, 0)

    x, y, w, h = en_iyi_dikdortgen

    margin_x = int(w * margin)

    yeni_x = x + margin_x
    yeni_w = max(1, w - (2 * margin_x))

    yeni_y = y
    yeni_h = h

    return (yeni_x, yeni_y, yeni_w, yeni_h)


def bant_maskesi_bul(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    yesil_mask = cv.inRange(hsv, altyesil, ustyesil)
    kernel = np.ones((10,10), np.uint8)
    yesil_mask = cv.morphologyEx(yesil_mask, cv.MORPH_CLOSE, kernel)
    yesil_mask = cv.morphologyEx(yesil_mask, cv.MORPH_OPEN, kernel)

    contours, _ = cv.findContours(yesil_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    gecerli_konturlar = [c for c in contours if cv.contourArea(c) > 3000]
    
    if not gecerli_konturlar:
        return None, None

    en_buyuk = max(gecerli_konturlar, key=cv.contourArea)
    if cv.contourArea(en_buyuk) < 5000:
        return None, None

    tekil_mask = np.zeros(yesil_mask.shape, dtype=np.uint8)
    cv.drawContours(tekil_mask, [en_buyuk], -1, 255, thickness=cv.FILLED)

    bx, by, bw, bh = en_buyuk_ikili_dikdortgen(tekil_mask)

    if bw <= 0 or bh <= 0:
        bx, by, bw, bh = cv.boundingRect(en_buyuk)

    bant_frame = frame[by : by + bh, bx : bx + bw]
    return bant_frame, (bx, by, bw, bh)


def objeleri_bul(bant_frame):
    bant_h, bant_w = bant_frame.shape[:2]
    gray = cv.cvtColor(bant_frame, cv.COLOR_BGR2GRAY)
    gray = cv.blur(gray, (3,3))

    edges = cv.Canny(gray, 81, 163)

    kernel = np.ones((15,15), np.uint8)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)
    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    
    filtrelenmis_konturlar = []
    kontur_gorseli = np.zeros((bant_h, bant_w), dtype=np.uint8)

    for c in contours:
        alan = cv.contourArea(c)

        if(alan < 5000):
            continue
        filtrelenmis_konturlar.append(c)
        cv.drawContours(kontur_gorseli, [c], -1, 255, thickness=cv.FILLED)

    return filtrelenmis_konturlar,kontur_gorseli, edges
 

def despill_yap(bgr, mask):
    bgr = bgr.astype(np.float32)
    b, g, r = cv.split(bgr)

    ortalama_rb = (r + b) / 2.0
    fazla_yesil = np.maximum(g - ortalama_rb, 0)
    g_temiz = g - fazla_yesil * 0.4

    bgr_temiz = cv.merge([b, g_temiz, r]).clip(0, 255).astype(np.uint8)
    b2, g2, r2 = cv.split(bgr_temiz)
    bgra = cv.merge([b2, g2, r2, mask])
    return bgra


def merkez_bul(x, y, w, h):
    return (x + w // 2, y + h // 2)


def mesafe(nokta1, nokta2):
    return np.sqrt((nokta1[0] - nokta2[0]) ** 2 + (nokta1[1] - nokta2[1]) ** 2)


def takibi_guncelle(takip_edilenler, anlik_merkezler, anlik_konturlar, sonraki_id, esik_mesafe=60, onay_esik=3, kayip_esik=5):
    kullanilan_id = set()
    yeni_sayilan = 0
    eslesen_idler = []

    for i, merkez in enumerate(anlik_merkezler):
        en_yakin_id = None
        en_yakin_mesafe = esik_mesafe
        guncel_kontur = anlik_konturlar[i] if i < len(anlik_konturlar) else None


        for obj_id, bilgi in takip_edilenler.items():
            if obj_id in kullanilan_id:
                continue
            kayitli_merkez = bilgi.get('merkez')
            if not isinstance(kayitli_merkez, (list, tuple)) or len(kayitli_merkez) < 2:
                continue

            d = mesafe(merkez, bilgi['merkez'])
            if d < en_yakin_mesafe:
                en_yakin_mesafe = d
                en_yakin_id = obj_id

        if en_yakin_id is not None:
            takip_edilenler[en_yakin_id]['onceki_merkez'] = takip_edilenler[en_yakin_id]['merkez']
            takip_edilenler[en_yakin_id]['merkez'] = merkez
            takip_edilenler[en_yakin_id]['kontur'] = guncel_kontur
            takip_edilenler[en_yakin_id]['gorulme'] += 1
            takip_edilenler[en_yakin_id]['kayip'] = 0
            kullanilan_id.add(en_yakin_id)
            eslesen_idler.append(en_yakin_id)
        else:
            takip_edilenler[sonraki_id] = {
                'merkez': merkez, 'onceki_merkez': merkez,
                'kontur': guncel_kontur, 'gorulme': 1, 'kayip': 0, 'sayildi': False
            }
            kullanilan_id.add(sonraki_id)
            eslesen_idler.append(sonraki_id)
            sonraki_id += 1

    for obj_id in list(takip_edilenler.keys()):
        if obj_id not in kullanilan_id:
            takip_edilenler[obj_id]['kayip'] += 1

    yeni_sayilan_idler = []
    for obj_id, bilgi in takip_edilenler.items():
        if bilgi['gorulme'] >= onay_esik:
            pass

    for obj_id in list(takip_edilenler.keys()):
        if takip_edilenler[obj_id]['kayip'] > kayip_esik:
            del takip_edilenler[obj_id]

    return takip_edilenler, sonraki_id, yeni_sayilan


def sticker_kaydet(frame, c, ofset_x, ofset_y, sayac, klasor="kaydedilen_objeler"):
    if not os.path.exists(klasor):
        os.makedirs(klasor)
        
    c_gercek = c.copy()
    c_gercek[:, :, 0] += ofset_x
    c_gercek[:, :, 1] += ofset_y

    rect = cv.minAreaRect(c_gercek)
    center, (box_w, box_h), angle = rect
    
    if box_w < box_h:
        angle += 90
        box_w, box_h = box_h, box_w

    h_frame, w_frame = frame.shape[:2]
    M_rot = cv.getRotationMatrix2D(center, angle, 1.0)
    frame_dondurulmus = cv.warpAffine(frame, M_rot, (w_frame, h_frame), flags=cv.INTER_LINEAR, borderMode=cv.BORDER_CONSTANT, borderValue=(0, 0, 0))

    c_float = c_gercek.astype(np.float32)
    n_points = c_float.reshape(-1, 1, 2)
    c_dondurulmus = cv.transform(n_points, M_rot).reshape(-1, 1, 2).astype(np.int32)

    x, y, w, h = cv.boundingRect(c_dondurulmus)
    
    padding = 20
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_frame, x + w + padding)
    y2 = min(h_frame, y + h + padding)

    sticker_bgr = frame_dondurulmus[y1:y2, x1:x2]
    if sticker_bgr.size == 0:
        return

    scale = 2
    bgr_h, bgr_w = sticker_bgr.shape[:2]
    mask = np.zeros((bgr_h * scale, bgr_w * scale), dtype=np.uint8)

    scaled_c = c_dondurulmus.copy().astype(np.float32)
    scaled_c[:, :, 0] = (scaled_c[:, :, 0] - x1) * scale
    scaled_c[:, :, 1] = (scaled_c[:, :, 1] - y1) * scale
    scaled_c = scaled_c.astype(np.int32)

    cv.drawContours(mask, [scaled_c], -1, 255, thickness=cv.FILLED)

    h_m, w_m = mask.shape
    parca_w = w_m // 8
    
    sol_parca = mask[:, :parca_w]
    sag_parca = mask[:, 7 * parca_w:]
    
    sol_piksel = cv.countNonZero(sol_parca)
    sag_piksel = cv.countNonZero(sag_parca)
    
    if sol_piksel < sag_piksel:
        sticker_bgr = cv.rotate(sticker_bgr, cv.ROTATE_180)
        mask = cv.rotate(mask, cv.ROTATE_180)

    sticker_bgr_large = cv.resize(sticker_bgr, (bgr_w * scale, bgr_h * scale), interpolation=cv.INTER_CUBIC)

    mask_cropped = grabcut_ile_inceltme(sticker_bgr_large, mask)
    sticker_bgra = despill_yap(sticker_bgr_large, mask_cropped)

    if sticker_bgra is None or sticker_bgra.size == 0:
        return

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


def grabcut_ile_inceltme(roi_bgr, kaba_maske, dilate_iter=8, erode_iter=4, grabcut_iter=5):
    if roi_bgr.size == 0 or kaba_maske.size == 0:
        return kaba_maske

    kernel = np.ones((3, 3), np.uint8)

    kesin_on = cv.erode(kaba_maske, kernel, iterations=erode_iter)

    olasi_bolge = cv.dilate(kaba_maske, kernel, iterations=dilate_iter)

    trimap = np.full(kaba_maske.shape, cv.GC_BGD, dtype=np.uint8)
    trimap[olasi_bolge > 0] = cv.GC_PR_BGD
    trimap[kaba_maske > 0] = cv.GC_PR_FGD  
    trimap[kesin_on > 0] = cv.GC_FGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv.grabCut(roi_bgr, trimap, None, bgd_model, fgd_model,
                   grabcut_iter, cv.GC_INIT_WITH_MASK)
    except cv.error:
        return kaba_maske

    ince_maske = np.where(
        (trimap == cv.GC_FGD) | (trimap == cv.GC_PR_FGD), 255, 0
    ).astype(np.uint8)

    soft_alpha = yumusak_alfa_uret(ince_maske)
    return soft_alpha


def yumusak_alfa_uret(ikili_maske, gecis_genisligi=4):
    dist_ic = cv.distanceTransform(ikili_maske, cv.DIST_L2, 5)
    ters_maske = cv.bitwise_not(ikili_maske)
    dist_dis = cv.distanceTransform(ters_maske, cv.DIST_L2, 5)

    alpha = np.zeros(ikili_maske.shape, dtype=np.float32)
    alpha[ikili_maske > 0] = 255
    gecis_bolgesi = (dist_dis > 0) & (dist_dis <= gecis_genisligi)
    alpha[gecis_bolgesi] = 255 * (1 - dist_dis[gecis_bolgesi] / gecis_genisligi)

    return alpha.astype(np.uint8)