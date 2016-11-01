import socket
import time
import happroc

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('192.168.1.201', 1001)
print('connecting to {} port {}'.format(*server_address))
sock.connect(server_address)

#otwieranie plików na dysku
# plik logów
plik = open("hapcan.txt",mode="a+")
#plik z opisem modułów
plik_mod = open("modules.txt",mode="r")

for pg in range(5):
    # utworzenie pustej ramki rozkazu
    ramka_str = "AA R1 R2 C1 C2 FF FF MM GG FF FF FF FF 00 A5"
    #odczytanie kolejnej lini pliku ini modules
    lin1=plik_mod.readline()
    #print('lini nr :  {!r}'.format(lin1))

    modul = (lin1[0:2])
    grupa = (lin1[2:4])
    ramka_str = ramka_str.replace("MM", modul)
    ramka_str = ramka_str.replace("GG", grupa)
    #print(ramka_str)
    # wpisanie rozkazu
    r1 = "10"
    r2 = "90"
    ramka_str = ramka_str.replace("R1", r1)
    ramka_str = ramka_str.replace("R2", r2)
    # wpisanie id komp
    idk1 = "FA"
    idk2 = "F0"
    ramka_str = ramka_str.replace("C1", idk1)
    ramka_str = ramka_str.replace("C2", idk2)
    #print(ramka_str)
    suma = happroc.hap_crc(ramka_str)
    #print('pusta :  {!r}'.format(mod_tmp))
    ramka_hpr = bytearray.fromhex(ramka_str)
    #print('pusta ramka:  {!r}'.format(ramka_hpr))

    ramka_hpr[13] = suma
    print('wysyłam ramkę:  {!r}'.format(ramka_hpr))
    sock.sendall(ramka_hpr)
    modul_r = ramka_hpr[7]
    grupa_r = ramka_hpr[8]
    #print(modul_r)
    #print(grupa_r)
    # a teraz co przyjdzie z powrotem
    # ile ramek spróbowac odczytać
    ile_ramek=18
    sukces=-256
    while ile_ramek > 0 :
        ile_ramek = ile_ramek -1
        data = sock.recv(15)
        sukces = happroc.spr_ramka(modul_r,grupa_r,data)
        if sukces > -255:
            print('sukces  :  {!r}'.format(sukces))
            tt1 = happroc.spr_temp(data[8], data[9])
            print(tt1)
            tekst = time.asctime() + ';' + str(tt1) + ' : ' + lin1 + '\n'
            plik.write(tekst)


sock.close()
plik.close()
plik_mod.close()

