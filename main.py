import cv2 as cv
import serial
import numpy as np

import bantObjeTespit as bot
import portBilgisiKontrolu as pbk

GSPEED_MODE_TO_MANUAL = "M310 0\r\n"

def main():
    ser = None
    kamera = None
    
    try:
        konveyor_port = pbk.konveyor_portu()
        if not konveyor_port:
            print("[HATA]: Konveyor portu bulunamadi! Cihazin bagli oldugundan emin olun.")
            return 
        ser = serial.Serial(konveyor_port, 115200, timeout=0.05)
        ser.write(GSPEED_MODE_TO_MANUAL.encode('utf-8'))
        print(f"[BILGI]: Konveyore manuel mod komutu gonderildi: {GSPEED_MODE_TO_MANUAL}")

        kamera_index = pbk.kamera_portu()
        if kamera_index is None:
            print("[HATA]: Aktif kamera bulunamadi!")
            return
        kamera = cv.VideoCapture(kamera_index, cv.CAP_DSHOW)

        kamera.set(cv.CAP_PROP_FPS, 30)
        kamera.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
        kamera.set(cv.CAP_PROP_FRAME_HEIGHT, 720)

        kamera_yukseklik = int(kamera.get(cv.CAP_PROP_FRAME_HEIGHT))
        orta_y = kamera_yukseklik // 2
        sticker_alinanlar = set()
        basarisiz_kare_sayaci = 0
        MAX_ARDISIK_HATA = 3

        toplam_obje_sayisi = 0
        takip_edilenler = {}
        sonraki_id = 0
        son_tespit_edilen_alan = 0
        sonraki_dosya_no = bot.baslangic_sayaci_bul()
        print(f"[BILGI]: Sticker kaydi {sonraki_dosya_no} numarasindan devam edecek.")

        print("[BILGI]: Konveyor bant araniyor...")
        bant_box = None

        while True:
            ret, frame = kamera.read()
            if not ret:
                continue
            
            _, bant_box = bot.bant_maskesi_bul(frame)
            if bant_box is not None:
                bx, by, bw, bh = bant_box
                print(f"[BILGI]: Bant basariyla sabitlendi! Kutu koordinatlari: {bant_box}")
                break

        bx, by, bw, bh = bant_box

        while True:
            if not kamera.isOpened():
                print("[HATA]: Kamera baglantisi kesildi!")
                break

            ret, rawframe = kamera.read()
            
            if not ret and rawframe is None:
                basarisiz_kare_sayaci += 1
                print(f"[UYARI]: Kameradan gecici sinyal alinamadi! ({basarisiz_kare_sayaci}/{MAX_ARDISIK_HATA})")
                
                if basarisiz_kare_sayaci >= MAX_ARDISIK_HATA:
                    print("[HATA]: Kamera baglantisiyla ilgili bir sorun var! Guvenli cikis yapiliyor.")
                    cv.destroyAllWindows()
                    break

                cv.waitKey(300)
                continue

            basarisiz_kare_sayaci = 0

            frame = rawframe.copy()
            bant_frame = rawframe[by:by+bh, bx:bx+bw].copy()


            anlik_merkezler = []
            anlik_konturlar = []

            cv.rectangle(frame, (bx, by), (bx+bw, by+bh), (255, 0, 0), 2)

            contours, kontur_gorseli, edges = bot.objeleri_bul(bant_frame)

            for c in contours:
                alan = cv.contourArea(c)
                    
                x, y, w, h = cv.boundingRect(c)

                global_x = x + bx
                global_y = y + by
    
                ust_kenar_mesafe = global_y - by
                alt_kenar_mesafe = (by + bh) - (global_y + h)
                
                if ust_kenar_mesafe < 50 or alt_kenar_mesafe < 50:
                    continue

                mx, my = bot.merkez_bul(global_x, global_y, w, h)
                anlik_merkezler.append((mx, my))
                anlik_konturlar.append(c)
                son_tespit_edilen_alan = alan

                global_c = c.copy()
                global_c[:, :, 0] += bx
                global_c[:, :, 1] += by
                
                cv.drawContours(frame, [global_c], -1, (255, 255, 255), thickness=cv.FILLED)


            takip_edilenler, sonraki_id, yeni_sayilan = bot.takibi_guncelle(
                 takip_edilenler, anlik_merkezler, anlik_konturlar, sonraki_id
            )

            if yeni_sayilan > 0:
                toplam_obje_sayisi += yeni_sayilan
                print(f"Yeni obje onaylandi! Toplam sayi: {toplam_obje_sayisi} | Son tespit edilen obje alani: {int(son_tespit_edilen_alan)} piksel")

            for obj_id, bilgi in takip_edilenler.items():
                if obj_id in sticker_alinanlar:
                    continue

                merkez_degeri = bilgi.get('merkez')
                onceki_merkez = bilgi.get('onceki_merkez')
                if not (isinstance(merkez_degeri, (list, tuple)) and len(merkez_degeri) > 1):
                    continue
                if not (isinstance(onceki_merkez, (list, tuple)) and len(onceki_merkez) > 1):
                    continue

                obj_merkez_y = merkez_degeri[1]
                onceki_merkez_y = onceki_merkez[1]
                
                c = bilgi.get('kontur')
                if c is None:
                    continue

                gecti_asagi = (onceki_merkez_y < orta_y) and (obj_merkez_y >= orta_y)
                gecti_yukari = (onceki_merkez_y > orta_y) and (obj_merkez_y <= orta_y)

                if gecti_asagi or gecti_yukari:
                    bot.sticker_kaydet(rawframe, c, bx, by, sonraki_dosya_no)
                    sonraki_dosya_no += 1
                    sticker_alinanlar.add(obj_id)
                    
                    toplam_obje_sayisi += 1
                    print(f"[BILGI]: Nesne (ID: {obj_id}) orta noktaya geldi, sticker kaydedildi. Toplam sayi: {toplam_obje_sayisi}")

                       
            cv.line(frame, (0, orta_y), (frame.shape[1], orta_y), (0, 255, 255), 1)

            cv.putText(frame, f"Toplam obje sayisi: {toplam_obje_sayisi}", (30,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)        
            
            cv.imshow("Canli kayit", frame)

            if cv.waitKey(1) & 0xFF == ord('q'):
                print("Kullanici tarafindan cikis yapildi!")
                break

    finally:
        if ser is not None:
            ser.close()
        if kamera is not None:
            kamera.release()
        cv.destroyAllWindows()
        cv.waitKey(1)

if __name__ == "__main__":
   main()