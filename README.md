# Hapcan
scripts in Python 3 for Hapcan BMS

[PL]


Co nowego: 
[ver 0.021 alpha]
- poprawiono bład obsługi przekaźników w Domoticzu
- dodano obsługę rolet poprzez procentowy moduł rolety w Domoticzu ('Blinds Percentage')
- drobne poprawki komunikatów

[ver 0.020 alpha]
- zmieniono i znacznie uproszczono dodawanie modułów i elementów systemu Hapcan - wystarczy obecnie wpisać spis wszystkich modułów w 1 zmiennej słownikowej oraz tylko w jednym miejscu przypisania poszczególnych elementów Hapcana do Domoticza - reszta tworzona jest dynamicznie
- zmieniono sposób tworzenia komunikatu do Hapcana - też tworzony dynamicznie a nie słownikowy
- dodano możliwość przesyłania danych temepratury do serwisu ThingSpeak

[ver. 0.013 alpha]
- dodano obsługę termostatów
- dodano obsługe błędów do logu tekstowego
- zmieniono czas odpytywania modułów - wszystkie po kolei co 2 sekundy a następnie co 100 sekund ponowienie sekwencji

[ver. 0.012 alpha]

- przekonstruowano w pętli 'czytaj' pobieranie ramek - najpierw szuka początkowego bajtu a potem dopiero pobiera resztę ramki
- sprawdza sumę kontrolną odebranej ramki
- poprawiono odczyt temeperatur
- wysyłanie zapytań do Hapcana co 10sek 1 kolejny moduł - wyeliminowało to tłok na magistrali CAN i teraz bez problemu pętla 'czytaj' radzi sobie z przykmowaniem ramek
- utworzono nowy słownik mapowań MAPOWANIE_MOD - gdzie umieszczone są wszystkie moduły odpytywane o stan
- wyeliminowano rozłączanie się pętli 'czytaj' poprzez rozdzielenie portów do odczytu i zapytań




