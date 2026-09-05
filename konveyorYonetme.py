global ser

GSPEED_MODE_TO_SERIAL = "M310 1\r\n"

def GSPEED_CMD(hiz):
    return f"M311 {hiz}\r\n"

def komut_gonder_ve_kontrol_et(komut_metni)-> bool:
    deneme_sayisi = 3
    for deneme in range(1, deneme_sayisi + 1):
        ser.write(komut_metni.encode('utf-8'))
        yanit = ser.readline().decode('utf-8', errors='ignore').strip()

        if yanit == "Ok":
            return True
        else:
            print(f"Deneme {deneme} yapiliyor... Gönderilen: {komut_metni.strip()}")
            print(f"Uyari: 'Ok' alinamadi. Gelen: '{yanit}'")
            
    print(f"\n[HATA]: 3 deneme sonucunda da 'Ok' yaniti alinamadi!")
    return False


def konveyor_calis(hiz)-> bool:
    if komut_gonder_ve_kontrol_et(GSPEED_MODE_TO_SERIAL):
        return komut_gonder_ve_kontrol_et(GSPEED_CMD(hiz))
    else:
        return False


def konveyor_dur()-> bool:
    if komut_gonder_ve_kontrol_et(GSPEED_CMD(0)):
        print("Konveyor guvenli bir sekilde durduruldu.")
        return True
    else:
        print("[KRITIK]: Konveyor durdurulamadi!")
        return False