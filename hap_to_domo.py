""""
Skrypt stanowi brame pomiedzy domoticzem a siecia HAPCAN - interfejs Ethernet
uruchomiony mosquitto
W domoticzu w sekcji sprzet dodajemy - MQTT Client Gateway with LAN interface port 1883 ip 127.0.0.1

uruchamiamy z konsoli: python3 hapcan_domo.py

"""
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

#Tutaj umieszczamy spis modułów naszego systemu
#formant (moduł,grupa):opis - możliwy zapis dziesiętny lub HEX
MAPOWANIE_MOD = {
    (1,10):'BUT kotłownia',
    (2,10):'BUT garaż',
    (25,11):'SW Tech 1',
}


# słownik opisujący nasz system Hapcan (moduł,grupa,kanał):(idx w Domoticzu, typ w Domoticzu, podtyp w Domoticzu
# dodatkowo można wykorzystać niektóre czujniki np. temeratury do zapisu do bazy ThingSpeac - wtedy należy dopisać dane pole_th - zgodne z nazwą w kanale i klucz czyli API key
#- możliwy zapis dziesiętny lub HEX
MAPOWANIE_HAP ={
    (0x1a, 0x0b, 0x01):{'idx':43,'dtype': 'Light/Switch', 'switchType': 'On/Off','pole_th':'field1', 'klucz_th': 'XXX'},
    (0x0a, 0x0b, 0x05):{'idx':45,'dtype': 'Light/Switch', 'switchType': 'Blinds Percentage'},
    (0x06, 0x0b, 0x11):{'idx':23,'dtype': 'Temp','stype': 'LaCrosse TX3'},
    (0x07, 0x0b, 0x14):{'idx':27,'dtype': 'Thermostat','stype': 'SetPoint'},
    (25,11,1):{'idx':37,'dtype': 'Light/Switch', 'switchType': 'On/Off'},
}

MAPOWANIE_DOM ={}
MAPOWANIE_MOD_SPS = {}
MAPOWANIE_THING = {}
IGNOROWANIE = {}

INDEKSY = {
    1:0 # # lista modułów do sprawdzenia
}
OKRES_CZASU = {
    1:1,  # flaga okresowego odczytu podstawowego - na początku i potem co x minut
    2:0,  # flaga okresowego odczytu 1x na dobę
    3:0,
}
#OKRES_CZASU[1] = 0





# utworzenie słownika idx Domoticza
ks = list(MAPOWANIE_HAP.keys())
#ks.sort()
#indeks=0
for key in ks:
    komendy = MAPOWANIE_HAP.get(key, None)
    idx = komendy['idx']
    map_temp = MAPOWANIE_HAP[key]
    map_temp2 = {'nodes':key}
    map_temp.update(map_temp2)
    #print("Klucze MAP to ::::::", MAPOWANIE_HAP[key], 'klucz', key)
    MAPOWANIE_DOM[idx]= map_temp
    #MAPOWANIE_HAP.update(map_temp)
    #indeks = indeks +1
    #komendy = MAPOWANIE_DOM.get(key, None)
    #print("Komenda to ...", komendy)
print("MAP HAP", MAPOWANIE_DOM)

indeks = 0
ks = list(MAPOWANIE_MOD.keys())
for key in ks:
    indeks = indeks +1
    map_temp ={'komunikat': 0x1090}
    list_temp = [0xf0, 0xf0, 0xff, 0xff]
    list_temp.append(key[0])
    list_temp.append(key[1])
    list_temp += [0xff, 0xff, 0xff, 0xff]
    map_temp2 = {'dane': list_temp}
    map_temp.update(map_temp2)
    #map_temp2.update(hex(key[0]))
    MAPOWANIE_MOD_SPS[indeks] = map_temp

print(MAPOWANIE_MOD_SPS)

@setInterval(2)
def odczyt_mod():
    okres_czasu = OKRES_CZASU.get(1)
    indeks_mod = INDEKSY.get(1)
    if OKRES_CZASU.get(1):
        indeks_mod = indeks_mod +1
        komenda = MAPOWANIE_MOD_SPS.get(indeks_mod, None)
        if komenda is not None:
            #print("komenda do wysłania do Hapcana", komenda)
            wyslij(komenda['komunikat'], komenda['dane'])
            INDEKSY[1] = indeks_mod
        else:
            INDEKSY[1]=0 # kasujemy licznik listy modułów do odczytu
            OKRES_CZASU[1]=0 # ustawiamy flagę następnego odczytu za 10 minut



@setInterval(60)  # Wysylanie zapytania do 100 sekund
def pytanie_o_status():
    print("pytanie_o_status do Hapcana",OKRES_CZASU, "Ignoruj", IGNOROWANIE)
    OKRES_CZASU[1]=1


def on_connect(client, userdata, flags, rc):
    print("Połączony z moskitem czyta domoticza... " + str(rc))
    client.subscribe("domoticz/out")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('ascii'))
        print("wiadomosc od Domoticza ", payload)
        idx = payload['idx']
        typ_idx = payload['dtype']
        nvalue = payload['nvalue']
        svalue1 = payload['svalue1']

    except ValueError:
        print("Błąd formatu json", str(msg))
        return
    #print("wiadomosc od Domoticza ", payload)

    if typ_idx == 'Light/Switch':
        typ_switch = payload['switchType']
        if typ_switch == 'Blinds Percentage':
            print ('a to była roleta')



    #print(IGNOROWANIE)
    # ignorowanie jest potrzebna gdzy nie ma mozliwosci rozroznienia z wiadowmosci czy dostajemy odpowiedz na nasza wiadomosc
    ignoruj = IGNOROWANIE.get(idx, 0)
    # print("ignoruj", ignoruj)
    if ignoruj is 0:
        komunikat= 0x10A0,
        dane = [0xF0, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF]
        # dane': [0xF0, 0xF0, 0x01, 0x01, 0x19, 0x0b, 0x00, 0xFF, 0xFF, 0xFF]},
        # znajdz komenda dla danego idx i nvalue
        #print("Otrzymałem od Domoticza", "idx", idx, "nvalue", nvalue, "svalue1", svalue1, payload)
        komendy = MAPOWANIE_DOM.get(idx, None)
        #klucz = (nvalue, svalue1)
        #print("komendy", komendy, "Klucz",klucz)
        if komendy is not None:
            nodes = komendy.get(('nodes'), None)
            #print("komenda do wysłania do Hapcana od Domoticza", komenda, "Payload", payload)
            if nodes is not None:
                # sprawdzenie jaki rodzaj urządzenia w Domoticzu
                if typ_idx == 'Light/Switch': # sprawdzamy czy switch
                    if typ_switch == 'On/Off': # tylko ON/OFF
                        dane[2]= nvalue
                        dane[3]=2**(nodes[2]-1)
                        dane[4]=nodes[0]
                        dane[5]=nodes[1]
                        print (dane)
                        wyslij(komunikat,dane)
                        #print("Wysylem ", komenda['komunikat'], komenda['dane'])
                # print("Wysylem ",komenda['komunikat'], komenda['dane'])
                 #wyslij(komenda['komunikat'], komenda['dane'])
    else:
        IGNOROWANIE[idx] = ignoruj - 1


def hap_crc(ramka):
    h_crc = 0
    for x in range(12):
        h_crc = h_crc + ramka[x + 1]
    h_crc = h_crc % 256
    return h_crc


def wyslij(id_komunikatu, dane):
    try:
        proto = socket.getprotobyname('tcp')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto)

        sock.connect(("192.168.1.201", 1001))

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

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = http.client.HTTPConnection("api.thingspeak.com:80")

    try:
        # 8. Ip i port modulu HAPCAN ethernet
        sock.connect(("192.168.1.201", 1002))

        while True:
            #resp = bytearray()
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
                            czas_pracy = OKRES_CZASU.get(3)
                            czas_pracy = czas_pracy+1
                            OKRES_CZASU[3] =czas_pracy
                        if resp[2] == 0x20 or resp[2] == 0x21:  # ramka przekaźnika
                            print("Ramka przekaźnika", )
                            komendy = MAPOWANIE_HAP.get((modul, grupa, id_urzadzenia), None)
                            if komendy is not None:
                                idx = komendy['idx']
                                print("Stan switcha",stan)
                                komenda = '{"idx": ' + str(idx) + ', "nvalue" : ' +str(stan) + ', "svalue" : "0"}'
                                IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                client.publish("domoticz/in", komenda)
                        if resp[2] == 0x40 or resp[2] == 0x41: # ramka przycisku
                            #print("Ramka przycisku",)
                            if resp[7] == 0x11: # ramka temperatury
                                komendy = MAPOWANIE_HAP.get((modul, grupa, id_urzadzenia), None)
                                if komendy is not None:
                                    idx = komendy['idx']
                                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                    tt1 = happroc.spr_temp(resp[8], resp[9])
                                    komenda = '{"idx": '+ str(idx) + ', "nvalue" : 0, "svalue" : "' + str(tt1) + '"}'
                                    #print("Komenda to ...",komenda)
                                    pole_th = komendy.get('pole_th',None)
                                    if pole_th is not None:
                                        print("Temp THING to ....",tt1,)
                                        klucz_th = komendy.get('klucz_th',None)
                                        params = urllib.parse.urlencode({pole_th : tt1, 'key': klucz_th})
                                        try:
                                            conn.request("POST", "/update", params, headers)
                                            response = conn.getresponse()
                                            data = response.read()
                                            #print('odpowiedź od Th',data)
                                        except Exception as bld:
                                            print("connection failed z Thingiem")
                                            plik = open("errory.log", mode="a+")
                                            plik.write(time.asctime() + ',' + str(bld) + '\n')
                                    client.publish("domoticz/in", komenda)
                                # teraz odczyt termostatu (id_urzadzenia ustawiony na 0x14)
                                id_urzadzenia = 0x14
                                komendy = MAPOWANIE_HAP.get((modul, grupa, id_urzadzenia), None)
                                if komendy is not None:
                                    idx = komendy['idx']
                                    IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                    tt1 = happroc.spr_temp(resp[10], resp[11])
                                    komenda = '{"idx": ' + str(idx) + ', "nvalue" : 0, "svalue" : "' + str(tt1) + '"}'
                                    #print("Komenda to ...", komenda)
                                    client.publish("domoticz/in", komenda)

                        if resp[2] == 0x70 or resp[2] == 0x71:  # ramka rolety
                            #print("Ramka rolety", procent)
                            komendy = MAPOWANIE_HAP.get((modul, grupa, id_urzadzenia), None)
                            if komendy is not None:
                                idx = komendy['idx']
                                IGNOROWANIE[idx] = IGNOROWANIE.get(idx, 0) + 1
                                procent = stan / 255 * 100
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
        conn.close()


if __name__ == "__main__":
    print("Start")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    # 7. ip i port mosquitto (domyslne ustawiania)
    client.connect("127.0.0.1", 1883, 60)

    client.loop_start()
    odczyt_mod() # wywołanie proedury odpytującej wszystkie moduły co 2
    pytanie_o_status() # wywołanie procedury wykonywanej co 10 minut
    #os.execvp('c:\Program Files(x86)\mosquitto\','mosquitto.exe')
    czytaj()




