"""
Wersja skryptu przerobiona na potrzeby starej wersji interfejsu LAN
- działa odczyt statusów z Hapcana i przesyła je do Domoticza

Przeróbki wymaga moduł odczytu danych z Domoticza - musiałby nie wysyłać bezpośrednio przez funkcję "wyślij" lecz zbierać np. do zmiennej słownikowej i wysyłać co minutę w momencie wystąpienia ramki czasu
na razie za mało czasu na taką przeróbkę [Z.]

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
import os

import socket
import binascii

import time

# dla Things
import http.client
import urllib
from urllib.parse import urlparse
import parser

import happroc



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
    # moduł 25,11
    (0x19, 0x0b, 0x01): {'idx': 37, 0xff: '{"command": "switchlight", "idx": 37, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 37, "switchcmd": "Off"}', },
    (0x19, 0x0b, 0x02): {'idx': 38, 0xff: '{"command": "switchlight", "idx": 38, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 38, "switchcmd": "Off"}', },
    (0x19, 0x0b, 0x03): {'idx': 39, 0xff: '{"command": "switchlight", "idx": 39, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 39, "switchcmd": "Off"}', },
    (0x19, 0x0b, 0x04): {'idx': 40, 0xff: '{"command": "switchlight", "idx": 40, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 40, "switchcmd": "Off"}', },
    (0x19, 0x0b, 0x05): {'idx': 41, 0xff: '{"command": "switchlight", "idx": 41, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 41, "switchcmd": "Off"}', },
    (0x19, 0x0b, 0x06): {'idx': 42, 0xff: '{"command": "switchlight", "idx": 42, "switchcmd": "On"}',
                         0x00: '{"command": "switchlight", "idx": 42, "switchcmd": "Off"}', },
  
    # (0x02, 0x01, 0x03):{'idx': 9, 0xff: '{"command": "switchlight", "idx": 9, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 9, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x04):{'idx': 10, 0xff: '{"command": "switchlight", "idx": 10, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 10, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x05):{'idx': 11, 0xff: '{"command": "switchlight", "idx": 11, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 11, "switchcmd": "Off"}',},
    # (0x02, 0x01, 0x06):{'idx': 12, 0xff: '{"command": "switchlight", "idx": 12, "switchcmd": "On"}', 0x00: '{"command": "switchlight", "idx": 12, "switchcmd": "Off"}',},

    # 2.zamieniamy nr modulu. grupa, kanal, idx w domoticzu ktoremu ma odpowiadac przycisk
    # modul, grupa, kanal przysicki (przycisk modul-05, grupa -07, kanaly od 01 d o08 - odpowiadaja idx domoticza od 13 do 20)
    #(0x01d, 0x0b, 0x06): {'idx': 10, 0xff: '{"command": "switchlight", "idx": 10, "switchcmd": "On"}',
    #                    0x00: '{"command": "switchlight", "idx": 10, "switchcmd": "Off"}', },
    # moduł, grupa, kanał - do temperatury
    (0x01, 0x0a, 0x11): {'idx':26},
    (0x02, 0x0a, 0x11): {'idx':25},
    (0x03, 0x0b, 0x11): {'idx':24},
    (0x06, 0x0b, 0x11): {'idx':18},
    (0x07, 0x0b, 0x11): {'idx':23},
    (0x08, 0x0b, 0x11): {'idx':20},
    (0x0b, 0x0b, 0x11): {'idx':21},
    (0x0c, 0x0b, 0x11): {'idx':22},
    (0xcf, 0x0b, 0x11): {'idx':19},
    # termostat
    (0x01, 0x0a, 0x14): {'idx':70},
    (0x02, 0x0a, 0x14): {'idx':71},
    (0x03, 0x0b, 0x14): {'idx':67},
    (0x06, 0x0b, 0x14): {'idx':68},
    (0x07, 0x0b, 0x14): {'idx':69},
    (0x08, 0x0b, 0x14): {'idx':72},
    (0x0b, 0x0b, 0x14): {'idx':73},
    (0x0c, 0x0b, 0x14): {'idx':74},
    (0xcf, 0x0b, 0x14): {'idx':75},
    # rolety
    (0x2a, 0x0e, 0x01): {"idx": 55, "nvalue" : 2, "svalue" : "90"},
    (0x2c, 0x0e, 0x02): {"idx": 56, "nvalue" : 2, "svalue" : "90"},
    (0x2c, 0x0e, 0x03): {"idx": 57, "nvalue" : 2, "svalue" : "90"},
    (0x29, 0x0e, 0x03): {"idx": 9, "nvalue" : 2, "svalue" : "90"},
    (0x2b, 0x0e, 0x01): {"idx": 58, "nvalue" : 2, "svalue" : "90"},
    (0x2b, 0x0e, 0x02): {"idx": 59, "nvalue" : 2, "svalue" : "90"},
    (0x2b, 0x0e, 0x03): {"idx": 60, "nvalue" : 2, "svalue" : "90"},
    (0x2c, 0x0e, 0x01): {"idx": 61, "nvalue" : 2, "svalue" : "90"},
    (0x2c, 0x0e, 0x02): {"idx": 62, "nvalue" : 2, "svalue" : "90"},
    (0x2c, 0x0e, 0x03): {"idx": 63, "nvalue" : 2, "svalue" : "90"},
    (0x28, 0x0e, 0x01): {"idx": 64, "nvalue" : 2, "svalue" : "90"},
    (0x28, 0x0e, 0x02): {"idx": 65, "nvalue" : 2, "svalue" : "90"},
    (0x28, 0x0e, 0x03): {"idx": 66, "nvalue" : 2, "svalue" : "90"},





}
# idx domoticza ma wyslac ramke do ethernet
MAPOWANIE_DOM = {

    # 3.zamieniamy kanal, numer modulu i grupe (tutaj 01,02)oraz idx w domoticzu ktoremu ma odpowiadac (tutaj od 7 do 12)
    #   numery przekaznikow - oznaczenia kanal 01-1 02-2 04-3 08-4 10-5 20-6

    #   przekazniki bistabilne sygnaly zal / wylacz
    # moduł 25,11
    37: {
        #                                               off/on kanal modul grupa
        (0, '0'): {'komunikat': 0x10A0, 'dane': [0xF0, 0xF0, 0x00, 0x01, 0x19, 0x0b, 0x00, 0xFF, 0xFF, 0xFF]},
        (1, '0'): {'komunikat': 0x10A0, 'dane': [0xF0, 0xF0, 0x01, 0x01, 0x19, 0x0b, 0x00, 0xFF, 0xFF, 0xFF]},
    },
 
    # 4.zamieniamy numer modulu i grupe oraz kanal (tutaj 05,07)oraz idx w domoticzu ktoremu ma odpowiadac (tutaj od 13 do 20)
    #   numery przyciskow - oznaczenia kanal 01-1 02-2 03-3 04-4 05-5 06-6 07-7 08-8

    #   przyciski sygnaly wcisniety / zwolniony
    10: {
        #                    modul  grupa           kanal   off/on
        (0, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0x00, 0xFF, 0xFF, 0xFF, 0xFF]},
        (1, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]},
    },
    13: {
        #                    modul  grupa           kanal   off/on
        (0, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0x00, 0xFF, 0xFF, 0xFF, 0xFF]},
        (1, '0'): {'komunikat': 0x3010, 'dane': [0x04, 0x02, 0xFF, 0xFF, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]},
    },

}
# słownik modułów do odpytania  {komenda sterująca, dane}
# dane [0xf0, 0xf0, 0xff, 0xff, MODUL, GRUPA, 0xff, 0xff, 0xff, 0xff
MAPOWANIE_MOD = {
    # Testowe
    #1: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x01, 0x0a, 0xff, 0xff, 0xff, 0xff]},
    #2: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x28, 0x0e, 0xff, 0xff, 0xff, 0xff]},
    #3: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x29, 0x0e, 0xff, 0xff, 0xff, 0xff]},
    #4: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x19, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    #5: {'komunikat': 0x1090, 'dane': [0xfa, 0xfa, 0xff, 0xff, 0x1c, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    # Przyciski
    1: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x01, 0x0a, 0xff, 0xff, 0xff, 0xff],'nazwa': 'BUT kotłownia'},
    2: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x02, 0x0a, 0xff, 0xff, 0xff, 0xff]},
    3: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x03, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    4: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x04, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    5: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x05, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    6: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x06, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    7: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x07, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    8: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x08, 0x0b, 0xff, 0xff, 0xff, 0xff]},
    9: {'komunikat': 0x1090, 'dane': [0xf0, 0xf0, 0xff, 0xff, 0x0b, 0x0b, 0xff, 0xff, 0xff, 0xff]},
   
}

MAPOWANIE_THING = {

}

IGNOROWANIE = {}

OKRES_CZASU = {
    1:0, # lista modułów do sprawdzenia
    2:0,  # flaga okresowego odczytu
    3:0,
}
OKRES_CZASU[1] = 0


def odczyt_mod():
    #print("co 10 sekund")
    okres_czasu = OKRES_CZASU.get(2)
    indeks_mod = OKRES_CZASU.get(1)
    #print("co 2 ")
    if okres_czasu == 0:
        indeks_mod = indeks_mod +1
        komenda = MAPOWANIE_MOD.get(indeks_mod, None)
        #print(okres_czasu)
        if komenda is not None:
            #print("komenda do wysłania do Hapcana", komenda)
            wyslij(komenda['komunikat'], komenda['dane'])
            OKRES_CZASU[1] = indeks_mod
        else:
            OKRES_CZASU[1]=0 # kasujemy licznik listy modułów do odczytu
            OKRES_CZASU[2]=1 # ustawiamy flagę następnego odczytu za 10 minut



def pytanie_o_status():
    print("pytanie_o_status do Hapcana",OKRES_CZASU, "Ignoruj", IGNOROWANIE)
    OKRES_CZASU[2]=0
    # 5.zamieniamy numer modulu i grupe na swoja (tu 01,02)
    # status przekaznikow                   modul grupa
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x01, 0x0a, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x02, 0x0a, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x03, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x06, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x07, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x08, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x0b, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0x0c, 0x0b, 0xff, 0xff, 0xff, 0xff])
    #wyslij(0x1090, [0xf0, 0xf0, 0xff, 0xff, 0xcf, 0x0b, 0xff, 0xff, 0xff, 0xff])
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


    #print(IGNOROWANIE)
    # ignorowanie jest potrzebna gdzy nie ma mozliwosci rozroznienia z wiadowmosci czy dostajemy odpowiedz na nasza wiadomosc
    ignoruj = IGNOROWANIE.get(idx, 0)
    # print("ignoruj", ignoruj)
    if ignoruj is 0:
        # znajdz komenda dla danego idx i nvalue
        #print("Otrzymałem od Domoticza", "idx", idx, "nvalue", nvalue, "svalue1", svalue1, payload)
        komendy = MAPOWANIE_DOM.get(idx, None)
        klucz = (nvalue, svalue1)
        #print("komendy", komendy, "Klucz",klucz)
        if komendy is not None:
            komenda = komendy.get((nvalue, svalue1), None)
            print("komenda do wysłania do Hapcana od Domoticza", komenda, "Payload", payload)
            if komenda is not None:
                 print("Wysylem ", komenda['komunikat'], komenda['dane'])
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
        #print("wyslij")
        proto = socket.getprotobyname('tcp')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)

        sock.connect(("192.168.1.201", 1001))
        # msg = bytearray.fromhex(toHex(id_komunikatu))
        #print("id hex = ", toHex(id_komunikatu))

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
    # główna pętla odczytująca status Hapcana z bramki LAN
    proto = socket.getprotobyname('tcp')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)

    try:
        # 8. Ip i port modulu HAPCAN ethernet
        sock.connect(("192.168.1.201", 1002))

        while True:
            resp = bytearray()
            resp = sock.recv(1)
            # teraz sprawdzi czy początek odebranego ciągu to początek ramki
            if resp[0] == 0xaa:
                #print("Resp !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",binascii.hexlify(resp) )
                for i in range(14):
                    resp += sock.recv(1)
                #print("nr 15",toHex(resp[14]))
                if hap_crc(resp) == resp[13]:
                    #print("Ramka się zgadza !!!!!!!!!!!!!!!!",binascii.hexlify(resp))
                    modul = resp[3]
                    grupa = resp[4]
                    id_urzadzenia = resp[7]
                    stan = resp[8]
                    if resp[1] == 0x30: #rozkaz stanu
                        #print("Rozkaz stanu", "to hex",toHex(resp[2]))
                        if resp[2] == 0x00: # ramka czasu
                            print("Ramka czasu",toHex(resp[3]),toHex(resp[4]) )
                            indeks_mod = OKRES_CZASU.get(1)
                            indeks_mod = indeks_mod + 1
                            komenda = MAPOWANIE_MOD.get(indeks_mod, None)
                            if komenda is not None:
                                id_komunikatu = komenda['komunikat']
                                dane = komenda['dane']
                                msg = bytearray()
                                msg.append(0xAA)
                                b2 = (id_komunikatu >> 8) & 0xFF;
                                msg.append(b2)
                                b1 = (id_komunikatu) & 0xFF;
                                msg.append(b1)
                                for val in dane:
                                    msg.append(val)
                                msg.append(hap_crc(msg))
                                msg.append(0xA5)
                                sock.sendall(msg)
                                print('wyslano =', binascii.hexlify(msg))
                                OKRES_CZASU[1] = indeks_mod
                            else:
                                OKRES_CZASU[1] = 0  # kasujemy licznik listy modułów do odczytu
                        if resp[2] == 0x20 or resp[2] == 0x21:  # ramka przekaźnika
                            #print("Ramka przekaźnika", )
                            komendy = MAPOWANIE_ETH.get((modul, grupa, id_urzadzenia), None)
                            if komendy is not None:
                                idx = komendy['idx']
                                komenda = komendy.get(stan, None)
                                if komenda is not None:
                                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                    #print("WYSYłAMY do domoticza stan przekaźnika", komenda)
                                    client.publish("domoticz/in", komenda)

                        if resp[2] == 0x40 or resp[2] == 0x41: # ramka przycisku
                            #print("Ramka przycisku",)
                            if resp[7] == 0x11: # ramka temperatury
                                komendy = MAPOWANIE_ETH.get((modul, grupa, id_urzadzenia), None)
                                if komendy is not None:
                                    idx = komendy['idx']
                                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                    tt1 = happroc.spr_temp(resp[8], resp[9])
                                    komenda = '{"idx": '+ str(idx) + ', "nvalue" : 0, "svalue" : "' + str(tt1) + '"}'
                                    #print("Komenda to ...",komenda)
                                    client.publish("domoticz/in", komenda)
                                # teraz odczyt termostatu (id_urzadzenia ustawiony na 0x14)
                                id_urzadzenia = 0x14
                                komendy = MAPOWANIE_ETH.get((modul, grupa, id_urzadzenia), None)
                                if komendy is not None:
                                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                    tt1 = happroc.spr_temp(resp[10], resp[11])
                                    idx = komendy['idx']
                                    komenda = '{"idx": ' + str(idx) + ', "nvalue" : 0, "svalue" : "' + str(tt1) + '"}'
                                    #print("Komenda to ...", komenda)
                                    client.publish("domoticz/in", komenda)


                        if resp[2] == 0x70 or resp[2] == 0x71:  # ramka rolety
                            procent = stan/255*100
                            #print("Ramka rolety", procent)
                            komendy = MAPOWANIE_ETH.get((modul, grupa, id_urzadzenia), None)
                            if komendy is not None:
                                idx = komendy['idx']
                                komenda = '{"idx": ' + str(idx) + ', "nvalue" : 2, "svalue" : "' + str(procent) + '"}'
                                #print("Komenda to ...", komenda)
                                client.publish("domoticz/in", komenda)
                            # teraz tu umieszczę dalszy program :)

    except socket.error as bld:
        print("Error?")
        plik = open("errory.log", mode="a+")
        plik.write(time.asctime()+ ',' + str(bld)+ '\n')
    except Exception as bld:
        plik = open("errory.log", mode="a+")
        plik.write(time.asctime() + ',' + str(bld) + '\n')
        #pass
    finally:
        plik.close()
        sock.close()


if __name__ == "__main__":
    print("Start")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    # 7. ip i port mosquitto (domyslne ustawiania)
    client.connect("127.0.0.1", 1883, 60)

    client.loop_start()
 
    czytaj()




