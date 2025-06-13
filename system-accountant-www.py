from flask import Flask, render_template, request, redirect, url_for
import os
import json

app = Flask(__name__)

DANE_PLIK = "dane.json"
HISTORIA_PLIK = "historia.txt"

# wczytywanie danych z pliku
def wczytaj_dane():
    if os.path.exists(DANE_PLIK):
        with open(DANE_PLIK, "r") as f:
            return json.load(f)
    return {"saldo": 0, "magazyn": {}}

# zapis danych do pliku
def zapisz_dane(dane):
    with open(DANE_PLIK, "w") as f:
        json.dump(dane, f)

# zapis historii operacji
def zapisz_historie(tekst):
    with open(HISTORIA_PLIK, "a") as f:
        f.write(tekst + "\n")

@app.route("/")
def index():
    dane = wczytaj_dane()
    return render_template("index.html", saldo=dane["saldo"], magazyn=dane["magazyn"])

@app.route("/zakup", methods=["POST"])
def zakup():
    nazwa = request.form["nazwa"]
    cena = float(request.form["cena"])
    ilosc = int(request.form["ilosc"])
    dane = wczytaj_dane()
    koszt = cena * ilosc
    if dane["saldo"] < koszt:
        return "Za mało środków!", 400
    dane["saldo"] -= koszt
    dane["magazyn"][nazwa] = dane["magazyn"].get(nazwa, 0) + ilosc
    zapisz_dane(dane)
    zapisz_historie(f"zakup,{nazwa},{cena},{ilosc}")
    return redirect(url_for("index"))

@app.route("/sprzedaz", methods=["POST"])
def sprzedaz():
    nazwa = request.form["nazwa"]
    ilosc = int(request.form["ilosc"])
    dane = wczytaj_dane()
    if dane["magazyn"].get(nazwa, 0) < ilosc:
        return "Za mało produktu w magazynie!", 400
    cena = float(request.form.get("cena", 0))  # opcjonalne
    dane["magazyn"][nazwa] -= ilosc
    dane["saldo"] += cena * ilosc
    zapisz_dane(dane)
    zapisz_historie(f"sprzedaz,{nazwa},{cena},{ilosc}")
    return redirect(url_for("index"))

@app.route("/saldo", methods=["POST"])
def saldo():
    wartosc = float(request.form["wartosc"])
    dane = wczytaj_dane()
    dane["saldo"] += wartosc
    zapisz_dane(dane)
    zapisz_historie(f"saldo,{wartosc}")
    return redirect(url_for("index"))

@app.route("/historia/")
@app.route("/historia/<int:start>/<int:end>/")
def historia(start=None, end=None):
    if not os.path.exists(HISTORIA_PLIK):
        return "Brak historii."
    with open(HISTORIA_PLIK, "r") as f:
        linie = f.readlines()
    liczba_linii = len(linie)
    if start is not None and end is not None:
        if start < 0 or end > liczba_linii or start >= end:
            return f"Niepoprawny zakres! Historia zawiera {liczba_linii} linii."
        linie = linie[start:end]
    return render_template("historia.html", historia=linie, liczba_linii=liczba_linii)

if __name__ == "__main__":
    app.run(debug=True)


