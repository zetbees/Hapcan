# Hapcan
scripts in Python 3 for Hapcan BMS

[PL]
[PL] ver. 0.012 alpha Wczesna faza skryptu

Co nowego: [ver. 0.012 alpha]

przekonstruowano w pętki 'czytaj' pobieranie ramek - najpierw szuka początkowego bajtu a potem dopiero pobiera resztę ramki
sprawdza sumę kontrolną odebranej ramki
poprawiono odczyt temeperatur
wysyłanie zapytań do Hapcana co 10sek 1 kolejny moduł - wyeliminowało to tłok na magistrali CAN i teraz bez problemu pętla 'czytaj' radzi sobie z przykmowaniem ramek
utworzono nowy słownik mapowań MAPOWANIE_MOD - gdzie umieszczone są wszystkie moduły odpytywane o stan
wyeliminowano rozłączanie się pętli 'czytaj' poprzez rozdzielenie portów do odczytu i zapytań
Zadania: sterowanie automatyką Hapcan za pomocą pliku z rozkazami odczytywanie danych z temperatury i zapis do bazy/logu zapis logów z systemu Hapcan

Problemy [do kompio] - częściowo wyeliminowane 

- używając Twojego skryptu też zdarzył mi się błąd formatu json - w momencie kliknięcia na przypisany switch w Domoticzu - konkretnie idx 11. Inne przyjmował bez problemu. (zrzut w pliku 'Java_Printing.pdf')
- problemem też było, że gdy włączał się interwał i zaczął wysyłać do Hapcana to przestał z niego odczytywać - mam wrażenie że zamknięcie socketu w procedurze wyślij rozłączało też socket w "czytaj" - próbowałem to zmodyfikować umieszczając "zmienną globalną 'Okres_czasu' ale nie do końca działało
- raz zdarzyło się że wystąpił błąd początku ramki - i potem wszystkie następne były przesunięte z tego względu próbowałem inaczej  napisać pętlę odczytu, aby odczytać 1 bajt, sprawdzić czy to xAA jeśli tak odczytać resztę 

