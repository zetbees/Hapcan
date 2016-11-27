"""
Wczesna wersja ale dziala 1
Wszystko uruchomione na Raspberry Pi, zainstalowany Domoticz, Python3, mosquitto
Skrypt stanowi brame pomiedzy domoticzem a siecia HAPCAN - interfejs Ethernet
uruchomiony mosquitto
W domoticzu w sekcji sprzet dodajemy - MQTT Client Gateway with LAN interface port 1883 ip 127.0.0.1

uruchamiamy z konsoli: python3 hapcan_domo.py

jesle sa bledy moze brakuje jakiego modulu do pythona np. paho.mqtt.client

w punktch 1-6 podmieniamy na nasze ustawienia HAPCAN i Domoticz
w punkcie 8 ustawiamy ip bramy HAPCAN ethernet

Na ta chwile dzialaja przyciski i przekazniki
do 30 sekund skrypt wysyla zapytanie o status, dzieki temu domoticz uaktualnia dane w razie zagubienia (ktos wlaczyl swiatlo a wlasnie resetowalismy malinke ;])

Wszystkie poprawki, modyfikacje oraz opytmalizacja kodu mile widziane
Nie wykluczone bledy :)
"""

# !/usr/bin/env python3

from __future__ import print_function
import paho.mqtt.client as mqtt
import json
import threading

import socket
import binascii


def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop():
                while not stopped.wait(interval):
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True
            t.start()
            return stopped

        return wrapper

    return decorator


# ramka ethernet zmienia status domoticza
MAPOWANIE_ETH = {
    # 1.zamieniamy nr modulu. grupa, kanal, idx w domoticzu ktoremu ma odpowiadac przekaznik
    # modul, grupa, kanal przekazniki (przekaznik modul-01, grupa -02, kanaly od 01 do 06 - odpowiadaja idx domoticza od 7 do 12)
    # (0x02, 0x01, 0x01):{'idx': 7, 0xff: '{"command": "switchlight", "idx": 7, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 7, "switchcmd": "Off"}',},
    (0x1c, 0x0b, 0x06): {'idx': 11, 0xff: '{"command": "switchlight", "idx": 11, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 11, "switchcmd": "Off"}', },
    # (0x02, 0x01, 0x03):{'idx': 9, 0xff: '{"command": "switchlight", "idx": 9, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 9, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x04):{'idx': 10, 0xff: '{"command": "switchlight", "idx": 10, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 10, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x05):{'idx': 11, 0xff: '{"command": "switchlight", "idx": 11, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 11, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x06):{'idx': 12, 0xff: '{"command": "switchlight", "idx": 12, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 12, "switchcmd": "Off"}',},

    # 2.zamieniamy nr modulu. grupa, kanal, idx w domoticzu ktoremu ma odpowiadac przycisk
    # modul, grupa, kanal przysicki (przycisk modul-05, grupa -07, kanaly od 01 d o08 - odpowiadaja idx domoticza od 13 do 20)
    (0x07, 0x0b, 0x06): {'idx': 10, 0xff: '{"command": "switchlight", "idx": 10, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 13, "switchcmd": "Off"}', },


}
# idx domoticza ma wyslac ramke do ethernet
MAPOWANIE_DOM = {

    # 3.zamieniamy kanal, numer modulu i grupe (tutaj 01,02)oraz idx w domoticzu ktoremu ma odpowiadac (tutaj od 7 do 12)
    #   numery przekaznikow - oznaczenia kanal 01-1 02-2 04-3 08-4 10-5 20-6

    #   przekazniki bistabilne sygnaly zal / wylacz
    11: {
        #                                               off/on kanal modul grupa
        (0, '0'): {'komunikat': 0x10A0, 'dane': [0xF0, 0xF0, 0x00, 0x06, 0x1c, 0x0b, 0x00, 0xFF, 0xFF, 0xFF]},
        (1, '0'): {'komunikat': 0x10A0, 'dane': [0xF0, 0xF0, 0x01, 0x06, 0x1c, 0x0b, 0x00, 0xFF, 0xFF, 0xFF]},
    },


    # 4.zamieniamy numer modulu i grupe oraz kanal (tutaj 05,07)oraz idx w domoticzu ktoremu ma odpowiadac (tutaj od 13 do 20)
    #   numery przyciskow - oznaczenia kanal 01-1 02-2 03-3 04-4 05-5 06-6 07-7 08-8

    #   przyciski sygnaly wcisniety / zwolniony
    10: {
        #                    modul  grupa           kanal   off/on
        (0, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0x00, 0xFF, 0xFF, 0xFF, 0xFF]},
        (1, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]},
    },

}
IGNOROWANIE = {}

OKRES_CZASU = {}
OKRES_CZASU[1] = 0

#@setInterval(10)  # Wysylanie zapytania do 100 sekund
def pytanie_o_status():

    OKRES_CZASU[1] = 1
    print("pytanie_o_status do Hapcana",OKRES_CZASU[1])
    # 5.zamieniamy numer modulu i grupe na swoja (tu 01,02)
    # status przekaznikow                   modul grupa
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x1c, 0x0b, 0xff, 0xff, 0xff, 0xff])
    # 6.zamieniamy numer modulu i grupe na swoja (tu 05,07)
    # status przyciskow                     modul grupa
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x07, 0x0b, 0xff, 0xff, 0xff, 0xff])


def on_connect(client, userdata, flags, rc):
    print("Połączony z moskitem czyta domoticza... " + str(rc))
    client.subscribe("domoticz/out")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('ascii'))
    except ValueError:
        print("Błąd formatu json", str(msg))
        return
    # print("wiadomosc", payload)
    idx = payload['idx']
    nvalue = payload['nvalue']
    svalue1 = payload['svalue1']

    print("Otrzymałem od Domoticza","idx", idx, "nvalue", nvalue, "svalue1", svalue1)
    # ignorowanie jest potrzebna gdzy nie ma mozliwosci rozroznienia z wiadowmosci czy dostajemy odpowiedz na nasza wiadomosc
    ignoruj = IGNOROWANIE.get(idx, 0)
    # print("ignoruj", ignoruj)
    if ignoruj is 0:
        # znajdz komenda dla danego idx i nvalue
        komendy = MAPOWANIE_DOM.get(idx, None)
        klucz = (nvalue, svalue1)
        # print("komendy", komendy, klucz)
        if komendy is not None:
            komenda = komendy.get((nvalue, svalue1), None)
            # print("komenda", komenda)
            if komenda is not None:
                # print("Wysylem ", komenda['komunikat'], komenda['dane'])
                # print("Wysylem ",komenda['komunikat'], komenda['dane'])
                wyslij(komenda['komunikat'], komenda['dane'])
    else:
        IGNOROWANIE[idx] = ignoruj - 1


def hap_crc(ramka):
    # ramka = bytearray.fromhex(ramka_str)
    h_crc = 0
    for x in range(12):
        h_crc = h_crc + ramka[x + 1]
    h_crc = h_crc % 256
    return h_crc


def wyslij(id_komunikatu, dane):
    try:
        # print("wyslij")
        proto = socket.getprotobyname('tcp')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)

        sock.connect(("192.168.1.201", 1001))
        # msg = bytearray.fromhex(toHex(id_komunikatu))
        print("id hex = ", toHex(id_komunikatu))

        msg = bytearray()
        msg.append(0xAA)
        # b4 = (id_komunikatu >> 24) & 0xFF;
        # print("4 hex = ", toHex(b4))
        # msg.append(b4)
        # msg.append(0x30)
        # b3 = (id_komunikatu >> 16) & 0xFF;
        # print("3 hex = ", toHex(b3))
        # msg.append(b3)
        # msg.append(0x10)
        b2 = (id_komunikatu >> 8) & 0xFF;
        # print("2 hex = ", toHex(b2))
        msg.append(b2)
        # msg.append(0x02)
        b1 = (id_komunikatu) & 0xFF;
        # print("1 hex = ", toHex(b1))
        msg.append(b1)
        # msg.append(0x01)

        for val in dane:
            msg.append(val)
        msg.append(hap_crc(msg))
        msg.append(0xA5)

        sock.sendall(msg)
        print('wyslano =', binascii.hexlify(msg))
        # sock.sendall(bytearray(b'\xaa\x10\x90\xf0\xf0\xff\xff\x02\x01\xff\xff\xff\xff}\xa5'))
    except socket.error:
        pass
    finally:
        sock.close()


def toHex(val):
    return '0x{:02x}'.format(val)


def czytaj():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    # 7. ip i port mosquitto (domyslne ustawiania)
    client.connect("127.0.0.1", 1883, 60)

    client.loop_start()

    pytanie_o_status()

    proto = socket.getprotobyname('tcp')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)

    try:
        # 8. Ip i port modulu HAPCAN ethernet
        sock.connect(("192.168.1.201", 1001))

        while 1:
            #resp = bytearray.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
            resp = bytearray()
            resp = sock.recv(2)
            # teraz sprawdzi czy początek odebranego ciągu to początek ramki
            # próbowałem odebrać recv(1) ale zgłaszał błąd 'IndexError: index out of range'
            if resp[1] != 0xaa:
                print("Resp !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", resp[0], resp[1])
                for i in range(13):
                    resp += sock.recv(1)
                print("nr 15",toHex(resp[14]))
                if hap_crc(resp) == resp[13]:
                    print("Ramka się zgadza !!!!!!!!!!!!!!!!")
                    # teraz tu umieszczę dalszy program :)




            print('z Hapcana ramka 15  = ', binascii.hexlify(resp))
            print("okres", OKRES_CZASU[1])
            if OKRES_CZASU[1] != 1 :
                print("Okres czasu !")
                OKRES_CZASU[1] = 0
                message = bytearray.fromhex("AA 10 90 FA F0 FF FF 07 0B FF FF FF FF 96 A5")
                print('sending {!r}'.format(message))
                sock.sendall(message)
            print("to hex",(resp[1]))

            # print(toHex(resp[2]))
            # print(toHex(resp[3]))
            # print(toHex(resp[4]))
            # print(toHex(resp[5]))
            # print(toHex(resp[6]))
            # print(toHex(resp[7]))
            # print(toHex(resp[8]))
            # print(toHex(resp[9]))
            modul = resp[3]
            if modul != 0x06:
                print("w h")
            grupa = resp[4]
            id_urzadzenia = resp[7]
            stan = resp[8]

            print("modul", toHex(modul), "grupa ", toHex(grupa), "kanal", toHex(id_urzadzenia), "stan", toHex(stan))

            komendy = MAPOWANIE_ETH.get((modul, grupa, id_urzadzenia), None)
            if komendy is not None:
                idx = komendy['idx']
                komenda = komendy.get(stan, None)
                if komenda is not None:
                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                    print("WYSYłAMY do domoticza!!!!" )
                    print(komenda)
                    client.publish("domoticz/in", komenda)
                    #komenda2='{"command": "switchlight", "idx": 11, "switchcmd": "On"}'
                    #client.publish("domoticz/in", komenda2)


    except socket.error:
        print("Error?")
        #pass
    finally:
        sock.close()


if __name__ == "__main__":
    print("Start")
    czytaj()




