# Hapcan
scripts in Python 3 for Hapcan BMS

[PL]
ver. 0001.0 alpha
Wczesna faza skryptu

Zadania:
sterowanie automatyką Hapcan za pomocą pliku z rozkazami
odczytywanie danych z temperatury i zapis do bazy/logu
zapis logów z systemu Hapcan

Znane problemy:
- gubi ramki :(
- nie zawsze dobrze odczytuje temperaturę
- problem z rodzajem zmeinnych : przypisanie zmniennej int do hex generuj błąd 

Problemy [do kompio]

- używając Twojego skryptu też zdarzył mi się błąd formatu json - w momencie kliknięcia na przypisany switch w Domoticzu - konkretnie idx 11. Inne przyjmował bez problemu. (zrzut w pliku 'Java_Printing.pdf')
- problemem też było, że gdy włączał się interwał i zaczął wysyłać do Hapcana to przestał z niego odczytywać - mam wrażenie że zamknięcie socketu w procedurze wyślij rozłączało też socket w "czytaj" - próbowałem to zmodyfikować umieszczając "zmienną globalną 'Okres_czasu' ale nie do końca działało
- raz zdarzyło się że wystąpił błąd początku ramki - i potem wszystkie następne były przesunięte z tego względu próbowałem inaczej  napisać pętlę odczytu, aby odczytać 1 bajt, sprawdzić czy to xAA jeśli tak odczytać resztę - lub też co w moim pliku main2 odczytywać póki nie pokaże się bajt xA5 a potem sprawdzić czy jest cała ramka. Niestety plik "main2" działa ale generuje ramki oderwane nieco od rzeczywistości (patrz plik "Java_Printing main2.pdf") z kolei próba implementacji fragmentu kodu do Twojego skryptu generuje błąd (Java_Printing błąd w haptodom2.pdf)

