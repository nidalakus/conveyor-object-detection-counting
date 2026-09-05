import cv2 as cv
import time
import serial

import konveyorYonetme as ky
import bantObjeTespit as bot
import portBilgisiKontrolu as pbk


def main():
    ser = None
    kamera = None
    
    try:
        konveyor_port = pbk.konveyor_portu()
        if not konveyor_port:
            print("[HATA]: Konveyor portu bulunamadi! Cihazin bagli oldugundan emin olun.")
            return 
        ser = serial.Serial(konveyor_port, 115200, timeout=0.05)
        ky.ser = ser

        kamera_index = pbk.kamera_portu()
        if kamera_index is None:
            print("[HATA]: Aktif kamera bulunamadi!")
            return
        kamera = cv.VideoCapture(kamera_index, cv.CAP_DSHOW)

        kamera.set(cv.CAP_PROP_FPS, 30)

        #gercek_max_fps = kamera.get(cv.CAP_PROP_FPS)
        #print(f"Kameranin 640x480 cozunurlukte destekledigi max FPS: {gercek_max_fps}")
        """yukseklik = kamera.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
        genislik = kamera.set(cv.CAP_PROP_FRAME_WIDTH, 320)
        print(yukseklik)
        print(genislik)"""

        anlik_gonderilen_hiz = -50
        ky.konveyor_calis(anlik_gonderilen_hiz)

        toplam_obje_sayisi = 0
        takip_edilenler = {}
        sonraki_id = 0
        son_obje_zamani = time.time()
        bos_gecen_sure = 5.0
        son_tespit_edilen_alan = 0
        sonraki_dosya_no = bot.baslangic_sayaci_bul()
        print(f"[BILGI]: Sticker kaydi {sonraki_dosya_no} numarasindan devam edecek.")


        while True:
            #t_kamera = time.time()
            ret, frame = kamera.read()

            if not ret:
                print("Kameradan goruntu alinamadi!")
                break

            #yUkseklik, gEnislik = frame.shape[:2]
            #print(f"Kare boyutu -> yukseklik: {yUkseklik}  genislik: {gEnislik}")

            #t_kamera_okuma = time.time() - t_kamera
            #print(f"kamera okuma suresi: {t_kamera_okuma}")

            #t_diger = time.time()
            bant_box, bant_sekli_mask, yesil_mask = bot.bant_maskesi_bul(frame)

            anlik_merkezler = []
            anlik_konturlar = []

            if bant_box is not None:
                bx, by, bw, bh = bant_box
                cv.rectangle(frame, (bx, by), (bx+bw, by+bh), (255, 0, 0), 2)
                contours, (ofset_x, ofset_y) = bot.objeleri_bul(frame, bant_box, bant_sekli_mask)
        
                for c in contours:
                    alan = cv.contourArea(c)
                    if alan > 300:
                        solidity = bot.solidity_hesapla(c)
                        if solidity < 0.55:   # deneyerek ayarla, 0.5-0.65 arasi iyi baslangic
                            continue 
                        x, y, w, h = cv.boundingRect(c)
                        mx, my = bot.merkez_bul(x + ofset_x, y + ofset_y, w, h)
                        anlik_merkezler.append((mx, my))
                        anlik_konturlar.append(c)
                        son_tespit_edilen_alan = alan
                        cv.rectangle(frame, (x+ofset_x, y+ofset_y),
                                             (x+w+ofset_x, y+h+ofset_y), (0, 255, 0), 2)
                        #cv.circle(frame, (mx, my), 4, (0, 0, 255), -1)
            else:
                print("Uyari: Yesil bant bu karede tespit edilemedi.")
                ofset_x, ofset_y = 0, 0

            takip_edilenler, sonraki_id, yeni_sayilan, eslesen_idler, yeni_sayilan_idler = bot.takibi_guncelle(
                 takip_edilenler, anlik_merkezler, sonraki_id
            )

            if yeni_sayilan > 0:
                toplam_obje_sayisi += yeni_sayilan
                for onaylana_id in yeni_sayilan_idler:
                    for idx, obj_id in enumerate(eslesen_idler):
                        if obj_id == onaylana_id:
                            bot.sticker_kaydet(frame, anlik_konturlar[idx], ofset_x,ofset_y, sonraki_dosya_no)
                            sonraki_dosya_no += 1
                            break
                print(f"Yeni obje onaylandi! Toplam sayi: {toplam_obje_sayisi} | Son tespit edilen obje alani: {int(son_tespit_edilen_alan)} piksel")

            cv.putText(frame, f"Toplam obje sayisi: {toplam_obje_sayisi}", (30,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)        

            aktif_obje_sayisi = len(anlik_merkezler)

            if aktif_obje_sayisi >= 3:
                hedef_hiz = -30
            elif aktif_obje_sayisi == 0:
                hedef_hiz = -80
            else:
                hedef_hiz = -50

            if hedef_hiz != anlik_gonderilen_hiz:
                basarili = ky.konveyor_calis(hedef_hiz)
                if basarili:
                    anlik_gonderilen_hiz = hedef_hiz
                    print(f"[HIZ AYARLANDI]: Aktif Obje: {aktif_obje_sayisi} -> Yeni Konveyor Hizi: {anlik_gonderilen_hiz}")
                else:
                    print("\n[KRITIK HATA]: Konveyor baglantisi koptu! Dongu durduruluyor...")
                    break
                    
            if aktif_obje_sayisi > 0:
                son_obje_zamani = time.time()
            else:
                gecen_sure = time.time() - son_obje_zamani
                if gecen_sure > bos_gecen_sure:
                    print(f"\n[UYARI]: {bos_gecen_sure} saniyedir bant üzerinde hic obje tespit edilmedi. Program sonlandiriliyor..")
                    break
            
            
            cv.imshow("Canli kayit", frame)
            if yesil_mask is not None:
                cv.imshow("Yesil Bant Maskesi", yesil_mask)

            #time.sleep(0.010)
            #t_diger = time.time() - t_diger
            #print(f"diger islemler suresi: {t_diger}")
            #toplam_sure = time.time() - t_kamera
            #
            # print(f"toplam sure: {toplam_sure}")
            
            if cv.waitKey(1) & 0xFF == ord('q'):
                print("Kullanici tarafindan cikis yapildi!")
                break

    finally:
        if ser is not None:
            ky.konveyor_dur()
            ser.close()
        if kamera is not None:
            kamera.release()
        cv.destroyAllWindows()

if __name__ == "__main__":
   main()