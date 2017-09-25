
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


def mailnij(tekst_maila,temat_maila):
    try:
        import smtplib
        from email.mime.text import MIMEText
        #
        sukces = -255
        config = configparser.ConfigParser()
        config.read('hapcan.ini')
        #pobiera dane z sekcji [mails] pliku .INI
        gmail_user = config.get('mails', 'gmail_user')
        gmail_password = config.get('mails', 'gmail_password')
        mail_to = config.get('mails', 'mail_to')
        msg = MIMEText(tekst_maila)
        msg['Subject'] = temat_maila
        msg['From'] = gmail_user
        msg['To'] = mail_to
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [mail_to], msg.as_string())
        print('Wysłano maila do : '+ mail_to)
        sukces=1
    except Exception as bld:
        print('Błąd podczas wysylania maila', bld)
        plik = open("errory.log", mode="a+")
        plik.write(time.asctime() + ',' + str(bld) + '\n')
        pass
    finally:
        server.quit()
    return sukces

def spr_status_domoticz():
    import requests
    import json
    from datetime import datetime
    sukces = -255
    try:
        config = configparser.ConfigParser()
        config.read('hapcan.ini')
        user_domo = config.get('domoticz', 'user')
        alert_time = int(config.get('domoticz', 'alert'))
        if len(user_domo):
            url = 'http://' + user_domo + ':' + config.get('domoticz', 'pass') + '@' + config.get(
            'domoticz', 'adres') + ':' + config.get('domoticz', 'port') + '/json.htm'
        else:
            url = 'http://' + config.get('domoticz', 'adres') + ':' + config.get('domoticz', 'port') + '/json.htm'
        postdata = {'type': 'devices', 'rid': config.get('domoticz', 'idx_spr')}
        headers = {'content-type': 'application/json'}
        resp = requests.get(url=url, params=postdata)
        dev_data = json.loads(resp.text)
        rez_temp = (dev_data['result'])
        dev_result = (rez_temp[-1])
        dev_last = dev_result['LastUpdate']
        datetime_object = datetime.strptime(dev_last, '%Y-%m-%d %H:%M:%S')
        data_obecna = datetime.now()
        spr_time =int(((data_obecna.timestamp() - datetime_object.timestamp()) / (60 * 60)))
        if spr_time > alert_time:
            print('Domoticz chyba nie działa')
        else:
            sukces=1
    except Exception as bld:
        print('Błąd podczas sprawdzania domoticz', bld)
        plik = open("errory.log", mode="a+")
        plik.write(time.asctime() + ',' + str(bld) + '\n')
        pass
    #finally:
        #
    return sukces






