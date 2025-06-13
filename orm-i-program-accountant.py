from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///firma.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Magazyn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), unique=True, nullable=False)
    ilosc = db.Column(db.Integer, nullable=False)

class Saldo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wartosc = db.Column(db.Float, nullable=False)

class Historia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    typ = db.Column(db.String(50), nullable=False)
    szczegoly = db.Column(db.String(200))
    data = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_first_request
def setup():
    db.create_all()
    if not Saldo.query.first():
        db.session.add(Saldo(wartosc=0))
        db.session.commit()

@app.route("/")
def index():
    saldo = Saldo.query.first().wartosc
    magazyn = Magazyn.query.all()
    return render_template("index.html", saldo=saldo, magazyn={m.nazwa: m.ilosc for m in magazyn})

@app.route("/zakup", methods=["POST"])
def zakup():
    nazwa = request.form["nazwa"]
    cena = float(request.form["cena"])
    ilosc = int(request.form["ilosc"])
    produkt = Magazyn.query.filter_by(nazwa=nazwa).first()
    saldo = Saldo.query.first()
    koszt = cena * ilosc

    if saldo.wartosc < koszt:
        return "Za mało środków!", 400

    try:
        saldo.wartosc -= koszt
        if produkt:
            produkt.ilosc += ilosc
        else:
            produkt = Magazyn(nazwa=nazwa, ilosc=ilosc)
            db.session.add(produkt)
        historia = Historia(typ="zakup", szczegoly=f"{nazwa},{cena},{ilosc}")
        db.session.add(historia)
        db.session.commit()
    except:
        db.session.rollback()
        return "Błąd transakcji.", 500

    return redirect(url_for("index"))

@app.route("/sprzedaz", methods=["POST"])
def sprzedaz():
    nazwa = request.form["nazwa"]
    cena = float(request.form["cena"])
    ilosc = int(request.form["ilosc"])
    produkt = Magazyn.query.filter_by(nazwa=nazwa).first()
    saldo = Saldo.query.first()

    if not produkt or produkt.ilosc < ilosc:
        return "Za mało produktu w magazynie!", 400

    try:
        produkt.ilosc -= ilosc
        saldo.wartosc += cena * ilosc
        historia = Historia(typ="sprzedaz", szczegoly=f"{nazwa},{cena},{ilosc}")
        db.session.add(historia)
        db.session.commit()
    except:
        db.session.rollback()
        return "Błąd transakcji.", 500

    return redirect(url_for("index"))

@app.route("/saldo", methods=["POST"])
def zmiana_salda():
    wartosc = float(request.form["wartosc"])
    saldo = Saldo.query.first()

    try:
        saldo.wartosc += wartosc
        historia = Historia(typ="saldo", szczegoly=f"{wartosc}")
        db.session.add(historia)
        db.session.commit()
    except:
        db.session.rollback()
        return "Błąd zmiany salda.", 500

    return redirect(url_for("index"))

@app.route("/historia/")
@app.route("/historia/<int:start>/<int:end>/")
def historia(start=None, end=None):
    historia_query = Historia.query.order_by(Historia.id).all()
    liczba_linii = len(historia_query)

    if start is not None and end is not None:
        if start < 0 or end > liczba_linii or start >= end:
            return f"Niepoprawny zakres! Historia zawiera {liczba_linii} linii."
        historia_query = historia_query[start:end]

    linie = [f"{h.typ},{h.szczegoly}" for h in historia_query]
    return render_template("historia.html", historia=linie, liczba_linii=liczba_linii)

if __name__ == "__main__":
    app.run(debug=True)
