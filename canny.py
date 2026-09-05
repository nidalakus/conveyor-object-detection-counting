import cv2 as cv
import numpy as np

import portBilgisiKontrolu as pbk


def hicbir_sey(x):
    pass


def canny_ayarlayici():
    kamera_index = pbk.kamera_portu()
    if kamera_index is None:
        print("[HATA]: Aktif kamera bulunamadi!")
        return

    kamera = cv.VideoCapture(kamera_index, cv.CAP_DSHOW)

    cv.namedWindow("Canny Kontroller", cv.WINDOW_NORMAL)
    cv.resizeWindow("Canny Kontroller", 420, 420)

    cv.createTrackbar("Sigma x100", "Canny Kontroller", 11, 100, hicbir_sey)
    cv.createTrackbar("Manuel (0/1)", "Canny Kontroller", 0, 1, hicbir_sey)
    cv.createTrackbar("Lower", "Canny Kontroller", 50, 255, hicbir_sey)
    cv.createTrackbar("Upper", "Canny Kontroller", 150, 255, hicbir_sey)
    cv.createTrackbar("Blur Ac (0/1)", "Canny Kontroller", 1, 1, hicbir_sey)
    cv.createTrackbar("Blur Kernel", "Canny Kontroller", 5, 21, hicbir_sey)
    cv.createTrackbar("Close Kernel", "Canny Kontroller", 5, 25, hicbir_sey)

    cv.createTrackbar("HSV-S Kullan (0/1)", "Canny Kontroller", 0, 1, hicbir_sey)
    cv.createTrackbar("S Lower", "Canny Kontroller", 50, 255, hicbir_sey)
    cv.createTrackbar("S Upper", "Canny Kontroller", 150, 255, hicbir_sey)

    print("Trackbar'lari ayarla, 's' ile degerleri yazdir, 'q' ile cik.")

    try:
        while True:
            ret, frame = kamera.read()
            if not ret:
                print("Kameradan goruntu alinamadi!")
                break

            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

            sigma = cv.getTrackbarPos("Sigma x100", "Canny Kontroller") / 100.0
            manuel = cv.getTrackbarPos("Manuel (0/1)", "Canny Kontroller")
            manuel_lower = cv.getTrackbarPos("Lower", "Canny Kontroller")
            manuel_upper = cv.getTrackbarPos("Upper", "Canny Kontroller")
            blur_ac = cv.getTrackbarPos("Blur Ac (0/1)", "Canny Kontroller")
            blur_k = cv.getTrackbarPos("Blur Kernel", "Canny Kontroller")
            close_k = max(1, cv.getTrackbarPos("Close Kernel", "Canny Kontroller"))

            hsv_kullan = cv.getTrackbarPos("HSV-S Kullan (0/1)", "Canny Kontroller")
            s_lower = cv.getTrackbarPos("S Lower", "Canny Kontroller")
            s_upper = cv.getTrackbarPos("S Upper", "Canny Kontroller")

            if blur_k % 2 == 0:
                blur_k += 1
            blur_k = max(1, blur_k)

            gray_islenmis = gray.copy()
            if blur_ac:
                gray_islenmis = cv.GaussianBlur(gray_islenmis, (blur_k, blur_k), 0)

            median = np.median(gray_islenmis)
            oto_lower = int(max(0, (1.0 - sigma) * median))
            oto_upper = int(min(255, (1.0 + sigma) * median))

            if manuel:
                lower, upper = manuel_lower, manuel_upper
            else:
                lower, upper = oto_lower, oto_upper
                cv.setTrackbarPos("Lower", "Canny Kontroller", lower)
                cv.setTrackbarPos("Upper", "Canny Kontroller", upper)

            edges_gray = cv.Canny(gray_islenmis, lower, upper)

            saturation = None
            edges_sat = None
            if hsv_kullan:
                hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
                saturation = hsv[:, :, 1]
                if blur_ac:
                    saturation = cv.GaussianBlur(saturation, (blur_k, blur_k), 0)
                edges_sat = cv.Canny(saturation, s_lower, s_upper)
                edges_ham = cv.bitwise_or(edges_gray, edges_sat)
            else:
                edges_ham = edges_gray

            edges_temiz = cv.dilate(edges_ham, None)
            edges_temiz = cv.erode(edges_temiz, None)
            edges_temiz = cv.morphologyEx(edges_temiz, cv.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))

            bilgi = frame.copy()
            mod_yazi = "MANUEL" if manuel else f"OTO(s={sigma:.2f})"
            blur_yazi = f"Blur:{blur_k}x{blur_k}" if blur_ac else "Blur:KAPALI"
            hsv_yazi = f"HSV-S:ACIK[{s_lower}-{s_upper}]" if hsv_kullan else "HSV-S:KAPALI"
            cv.putText(bilgi, f"{mod_yazi} Gray:[{lower}-{upper}] {blur_yazi}",
                       (10, 22), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv.putText(bilgi, f"{hsv_yazi} Close:{close_k}",
                       (10, 45), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv.imshow("Kamera", bilgi)
            cv.imshow("Canny Gray", edges_gray)
            if saturation is not None:
                cv.imshow("Saturation Kanali", saturation)
                cv.imshow("Canny Saturation", edges_sat)
            else:
                if cv.getWindowProperty("Saturation Kanali", cv.WND_PROP_VISIBLE) >= 1:
                    cv.destroyWindow("Saturation Kanali")
                if cv.getWindowProperty("Canny Saturation", cv.WND_PROP_VISIBLE) >= 1:
                    cv.destroyWindow("Canny Saturation")
            cv.imshow("Canny Birlesik (Ham)", edges_ham)
            cv.imshow("Canny Temizlenmis", edges_temiz)

            tus = cv.waitKey(1) & 0xFF
            if tus == ord('q'):
                break
            elif tus == ord('s'):
                print("\n--- KAYDEDILEN DEGERLER ---")
                if manuel:
                    print(f"gray_lower = {lower}")
                    print(f"gray_upper = {upper}")
                else:
                    print(f"sigma = {sigma:.2f}")
                    print(f"# median'a gore hesaplanan: gray_lower={lower}, gray_upper={upper}")
                print(f"blur_ac = {bool(blur_ac)}")
                print(f"blur_kernel = ({blur_k}, {blur_k})")
                print(f"close_kernel = ({close_k}, {close_k})")
                print(f"hsv_saturation_kullan = {bool(hsv_kullan)}")
                if hsv_kullan:
                    print(f"s_lower = {s_lower}")
                    print(f"s_upper = {s_upper}")
                print("----------------------------\n")

    finally:
        kamera.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    canny_ayarlayici()