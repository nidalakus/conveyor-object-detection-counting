import cv2 as cv
import numpy as np
 
import portBilgisiKontrolu as pbk
 
 
def hicbir_sey(x):
    pass
 
 
def main():
    kamera_index = pbk.kamera_portu()
    if kamera_index is None:
        print("[HATA]: Aktif kamera bulunamadi!")
        return
 
    kamera = cv.VideoCapture(kamera_index, cv.CAP_DSHOW)
    kamera.set(cv.CAP_PROP_FPS, 30)
 
    cv.namedWindow("Kontroller", cv.WINDOW_NORMAL)
    cv.resizeWindow("Kontroller", 400, 300)
 
    # Mevcut bantObjeTespit.py degerlerini baslangic noktasi olarak kullaniyoruz
    cv.createTrackbar("H alt", "Kontroller", 43, 179, hicbir_sey)
    cv.createTrackbar("H ust", "Kontroller", 78, 179, hicbir_sey)
    cv.createTrackbar("S alt", "Kontroller", 52, 255, hicbir_sey)
    cv.createTrackbar("S ust", "Kontroller", 255, 255, hicbir_sey)
    cv.createTrackbar("V alt", "Kontroller", 35, 255, hicbir_sey)
    cv.createTrackbar("V ust", "Kontroller", 255, 255, hicbir_sey)
 
    # Morphology kernel boyutunu da canli test edebilmek icin
    cv.createTrackbar("Kernel", "Kontroller", 7, 25, hicbir_sey)
 
    print("Trackbar'lari ayarla, 's' ile kaydet/yazdir, 'q' ile cik.")
 
    try:
        while True:
            ret, frame = kamera.read()
            if not ret:
                print("Kameradan goruntu alinamadi!")
                break
 
            h_alt = cv.getTrackbarPos("H alt", "Kontroller")
            h_ust = cv.getTrackbarPos("H ust", "Kontroller")
            s_alt = cv.getTrackbarPos("S alt", "Kontroller")
            s_ust = cv.getTrackbarPos("S ust", "Kontroller")
            v_alt = cv.getTrackbarPos("V alt", "Kontroller")
            v_ust = cv.getTrackbarPos("V ust", "Kontroller")
            kernel_boyut = max(1, cv.getTrackbarPos("Kernel", "Kontroller"))
 
            alt = np.array([h_alt, s_alt, v_alt])
            ust = np.array([h_ust, s_ust, v_ust])
 
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            mask = cv.inRange(hsv, alt, ust)
 
            kernel = np.ones((kernel_boyut, kernel_boyut), np.uint8)
            mask_temiz = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
            mask_temiz = cv.morphologyEx(mask_temiz, cv.MORPH_OPEN, kernel)
 
            # Maskeyi orijinal goruntu uzerine bindirerek de gosterelim,
            # boylece hangi bolgelerin "kacirildigini" daha net gorursun
            renkli_maske = cv.bitwise_and(frame, frame, mask=mask_temiz)
 
            # Bilgi metni
            bilgi = frame.copy()
            cv.putText(bilgi, f"H:[{h_alt}-{h_ust}] S:[{s_alt}-{s_ust}] V:[{v_alt}-{v_ust}] K:{kernel_boyut}",
                       (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
 
            cv.imshow("Kamera", bilgi)
            cv.imshow("Ham Maske", mask)
            cv.imshow("Temizlenmis Maske", mask_temiz)
            cv.imshow("Maskeli Goruntu", renkli_maske)
 
            tus = cv.waitKey(1) & 0xFF
            if tus == ord('q'):
                break
            elif tus == ord('s'):
                print("\n--- KAYDEDILEN DEGERLER ---")
                print(f"altyesil = np.array([{h_alt}, {s_alt}, {v_alt}])")
                print(f"ustyesil = np.array([{h_ust}, {s_ust}, {v_ust}])")
                print(f"kernel = np.ones(({kernel_boyut},{kernel_boyut}), np.uint8)")
                print("----------------------------\n")
 
    finally:
        kamera.release()
        cv.destroyAllWindows()
 
 
if __name__ == "__main__":
    main()
 










