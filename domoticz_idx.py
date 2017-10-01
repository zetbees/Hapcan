import requests
import json
import configparser
import csv

# utworzenie słownika MAP_DOMO
MAP_DOMO = {}

try:
    config = configparser.ConfigParser()
    config.read('hapcan.ini')
    user_domo=config.get('domoticz','user')
    if len(user_domo):
        url = 'http://' + user_domo + ':' + config.get('domoticz', 'pass') + '@' + config.get('domoticz', 'adres') + ':' + config.get('domoticz', 'port') + '/json.htm'
    else:
        url = 'http://'+config.get('domoticz', 'adres') + ':' + config.get('domoticz', 'port') + '/json.htm'

    postdata ={'type':'devices','filter' : 'all','used' : 'true','order' : 'Type'}

    resp = requests.get(url=url, params=postdata)
    domoticz_dane_json = json.loads(resp.text)
    # odczyt danych z poszczególnych urządzeń
    domoticz_result = (domoticz_dane_json['result'])

# odczyt nagłówków z pliku domoticz_idx - nagłówki to etykiety z urządzeń Domoticza które chcemy odczytać
    with open('domoticz_idx.csv','r') as  csvfile:
        dane_csv = csv.reader(csvfile, delimiter=';')
        domoticz_head = next(dane_csv)
    csvfile.close()

# zapisanie danych w formie słownika (z nagłówkiem)
    with open('domoticz_idx.csv', 'w', newline='') as csvfile:
        dane_csv = csv.DictWriter(csvfile, fieldnames=domoticz_head, delimiter=';')
        dane_csv.writeheader()
        for x in domoticz_result:
            for key in domoticz_head:
                res_key = x[key]
                dic_temp = {key: res_key}
                MAP_DOMO.update(dic_temp)
            dane_csv.writerow(MAP_DOMO)
    csvfile.close()

except KeyError:
    print('Nieprawidłowy plik *.ini lub brak odpowiedniej wartości w nim - SPRAWDŹ')
    exit()

except Exception as blad:
    print('Błąd inny', blad, Exception)
    exit()