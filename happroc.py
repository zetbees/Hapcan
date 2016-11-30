
def spr_temp(tempmsb,templsb):
    #funkcja odczytująca wartość temperatur z ramki
    temp = 0
    # sprawdzenie 3 bitów w starszym byte temperatury
    for bit_nr in range(3):
        if (tempmsb & (1 << bit_nr)):
            temp = temp + 2 ** (bit_nr + 4)
    # sprawdzenie 4 starszych bitów w młodszym byte temperatury
    for bit_nr in range(4):
        if (templsb & (1 << (bit_nr + 4))):
            temp = temp + 2 ** (bit_nr)
    # sprawdzenie 4 młodszych bitów w młodszym byte temperatury
    for bit_nr in range(4):
        if (templsb & (1 << (bit_nr))):
            temp = temp + 2 ** (bit_nr - 4)
    # sprawdzenie znaku temperatury +/-
    if (tempmsb & (1 << 4)):
        temp = temp * (-1)
    return temp


def hap_crc(ramka_str):
    ramka = bytearray.fromhex(ramka_str)
    h_crc=0
    for x in range(12):
        h_crc = h_crc + ramka[x+1]
    h_crc = h_crc % 256
    return h_crc




def spr_ramka(modul_r,grupa_r,data):

    sukces=-255
    # sprawdzam pierwszy byte ramki

    ch_data = data[0]
    if ch_data == 0xaa:
        try:
            if (data[1]) == 0x30 and (data[2] == 0x41 and data[7] == 0x11):
                print("JEST !!!:  ", end='')
                sukces = 1
                if (data[3] == modul_r and data[4] == grupa_r):
                    print("super!!!")
        except:
            print('Bład długości ramki')

    return sukces





