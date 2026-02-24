# Kosmiczna Strzelanka 2D – Roguelite Arcade 🚀

Dynamiczna, dwuwymiarowa gra zręcznościowa napisana w języku Python przy użyciu biblioteki Pygame. 
Projekt łączy klasyczną mechanikę "bullet hell" z nowoczesnymi elementami roguelite, takimi jak meta-progresja, klasy statków oraz sklep z ulepszeniami.

Gra została stworzona jako projekt zaliczeniowy, demonstrujący zaawansowane wykorzystanie programowania obiektowego (OOP) oraz efektywną współpracę z modelami generatywnej sztucznej inteligencji (Google Gemini).

## ✨ Główne cechy gry
* **Tryb Singleplayer i Local Co-op:** Graj sam lub zaproś znajomego do gry na jednej klawiaturze!
* **Klasy Statków:** Wybierz jeden z trzech statków (Lekki, Zbalansowany, Ciężki) różniących się prędkością, ilością punktów życia (HP) i odnowieniem uniku.
* **Meta-progresja (Sklep):** Zbieraj monety podczas gry i wydawaj je w menu głównym na stałe ulepszenia (zwiększenie maksymalnego HP, wyższy poziom startowy).
* **System Walki i Combo:** Unikaj ciosów za pomocą Dasha (I-frames), zbieraj Power-Upy (Tarcza, Rapid-fire, Shotgun, Laser) i nabijaj mnożnik Combo za szybkie eliminacje.
* **Proceduralne Audio i Efekty:** Gra **nie wymaga** żadnych zewnętrznych plików dźwiękowych! Wszystkie efekty (wybuchy, strzały, fanfary) oraz muzyka w tle są generowane
*  matematycznie w locie (synteza fal). Całości dopełnia trzęsienie ekranu (Screen Shake) i autorski system cząsteczek (Particles).
* **Trwały Ranking (Leaderboard):** System zapisuje 10 najlepszych wyników wraz z nazwami graczy w pliku JSON.

## 💻 Wymagania systemowe
Aby uruchomić grę, potrzebujesz zainstalowanego środowiska Python (wersja 3.8 lub nowsza) oraz biblioteki Pygame.

1. Pobierz i zainstaluj [Python](https://www.python.org/downloads/).
2. Otwórz wiersz poleceń (Terminal / CMD / PowerShell) i zainstaluj bibliotekę Pygame, wpisując poniższą komendę:
   ```bash
   pip install pygame
   Instrukcja uruchomienia
   
🚀Instrukcja uruchomienia
Pobierz lub sklonuj repozytorium z grą na swój dysk.

Otwórz terminal w folderze z projektem.

Uruchom plik główny poleceniem:

Bash
python game.py
(Opcjonalnie: Możesz utworzyć skrót Windows uruchamiający grę przez pythonw.exe game.py, aby ukryć okno konsoli).

 
🎮 Sterowanie
Menu i Interfejs:
Myszka: Wybór opcji w menu głównym, sklepie i ekranie pauzy.
ESC: Pauza w trakcie gry / Wznowienie gry / Powrót do menu.
ENTER: Zapisanie wyniku na ekranie końcowym.
Gracz 1 (Niebieski):
Ruch: Klawisze W, A, S, D
Celowanie: Kursor myszy (automatyczny ostrzał)
Unik (Dash): SPACJA
Gracz 2 (Różowy - Tryb Co-op):
Ruch: Strzałki na klawiaturze (Góra, Dół, Lewo, Prawo)
Celowanie: Automatyczne (namierza najbliższego wroga)
Unik (Dash): Prawy CTRL






