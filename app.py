# from flask import Flask, render_template
# from flask_bootstrap import Bootstrap
# app = Flask(__name__)


# @app.route("/")
# def index():
#     return render_template('index.html')

from flask import Flask, render_template, request, g
# from flask_bootstrap import Bootstrap
import requests
from random import randint
import sqlite3
from collections import defaultdict

app = Flask(__name__)



def connect_db():
    sql = sqlite3.connect('gminy.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite3'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


# ściaga kurs NBP ze strony
def kurs():
    global kurs
    response = requests.get("http://api.nbp.pl/api/exchangerates/rates/a/eur/")
    data = response.json()
    dane = data['rates']
    kurs = dane[0]['mid']
    kurs = float(kurs)
    return kurs


# ściaga datę kursu NBP ze strony
def data():
    response = requests.get("http://api.nbp.pl/api/exchangerates/rates/a/eur/")
    data = response.json()
    dane = data['rates']
    date = dane[0]['effectiveDate']
    return date


# klasa dla kalkulatora nr 1
class Kalkulator:

    def __init__(self, waluta, value, size, region, intensity, pp):
        self.waluta = waluta
        self.value = value
        self.size = size
        self.region = region
        self.intensity = intensity
        self.pp = pp

    def intensity2(self):
        if (self.region == 'lubuskie' or self.region == 'zachodniopomorskie') and self.size == 'duży':
            intensity = 0.35
        elif (self.region == 'lubuskie' or self.region == 'zachodniopomorskie') and self.size == 'średni':
            intensity = 0.45
        elif (self.region == 'lubuskie' or self.region == 'zachodniopomorskie') and (self.size == 'mikro' or self.size == 'mały'):
            intensity = 0.55
        elif self.region == 'wielkopolskie' and self.size == 'duży':
            intensity = 0.25
        elif self.region == 'wielkopolskie' and self.size == 'średni':
            intensity = 0.35
        else:
            intensity = 0.45
        return intensity

    def cur(self):
        if self.value > 100000000 and self.region == 'wielkopolskie':
            pp = 0.25 * (50000000 + 0.5 * 50000000)
        elif self.value > 100000000 and self.region == 'lubuskie':
            pp = 0.35 * (50000000 + 0.5 * 50000000)
        elif self.value > 100000000 and self.region == 'zachodniopomorskie':
            pp = 0.35 * (50000000 + 0.5 * 50000000)
        elif 100000000 >= self.value > 50000000:
            b = self.value - 50000000
            pp = self.intensity * (50000000 + 0.5 * b)
        elif 50000000 >= self.value > 0:
            pp = self.intensity * self.value
        else:
            pp = 123456789
        return pp

    def notify(self):
        if self.value > 100000000:
            notification = True
        else:
            notification = False
        return notification

    def criteria(self):
        db = get_db()
        if self.waluta == "EURO":
            self.value *= cena
        else:
            pass

        if self.size == 'średni':
            mycursor = db.execute(
                f'SELECT * FROM gminy WHERE wojewodztwo="{self.region}" and nakladys <= {self.value}')
            powiat = mycursor.fetchall()
            gminy = []
            for i in powiat:
                gminy.append(i[2])
            powiaty = []
            for i in powiat:
                powiaty.append(i[1])
            dic = {}
            for i in range(len(gminy)):
                dic[gminy[i]] = powiaty[i]
            if self.waluta == "EURO":
                self.value /= cena

        elif self.size == 'mały':
            mycursor = db.execute(
                f'SELECT * FROM gminy WHERE wojewodztwo="{self.region}" and nakladyma <= {self.value}')
            powiat = mycursor.fetchall()
            gminy = []
            for i in powiat:
                gminy.append(i[2])
            powiaty = []
            for i in powiat:
                powiaty.append(i[1])
            dic = {}
            for i in range(len(gminy)):
                dic[gminy[i]] = powiaty[i]
            if self.waluta == "EURO":
                self.value /= cena

        elif self.size == 'mikro':
            mycursor = db.execute(
                f'SELECT * FROM gminy WHERE wojewodztwo="{self.region}" and nakladym <= {self.value}')
            powiat = mycursor.fetchall()
            gminy = []
            for i in powiat:
                gminy.append(i[2])
            powiaty = []
            for i in powiat:
                powiaty.append(i[1])
            dic = {}
            for i in range(len(gminy)):
                dic[gminy[i]] = powiaty[i]
            if self.waluta == "EURO":
                self.value /= cena

        else:
            mycursor = db.execute(
                f'SELECT * FROM gminy WHERE wojewodztwo="{self.region}" and naklady <= {self.value}')
            powiat = mycursor.fetchall()
            gminy = []
            for i in powiat:
                gminy.append(i[2])
            powiaty = []
            for i in powiat:
                powiaty.append(i[1])
            dic = {}
            for i in range(len(gminy)):
                dic[gminy[i]] = powiaty[i]
            if self.waluta == "EURO":
                self.value /= cena

        return dic

    def gn(self):
        db = get_db()
        mycursor = db.execute(
            f'SELECT * FROM gminy WHERE wojewodztwo="{self.region}"')
        dane = mycursor.fetchall()

        gminy = []
        for i in dane:
            gminy.append(i[2])

        if self.size == 'duży':
            nak = []
            for i in dane:
                nak.append(i[3])
        elif self.size == 'średni':
            nak = []
            for i in dane:
                nak.append(i[4])
        elif self.size == 'mały':
            nak = []
            for i in dane:
                nak.append(i[5])
        else:
            nak = []
            for i in dane:
                nak.append(i[6])

        dicn = {}
        for i in range(len(gminy)):
            dicn[gminy[i]] = nak[i]

        return dicn


class Where:

    def __init__(self, currency, value, size, rd):
        self.currency = currency
        self.value = value
        self.size = size
        self.rd = rd

    def lubuskie(self):
        if self.rd == 'option1' and self.size != 'mikro':
            naklady = 'nakladybr'
        elif self.size == 'duży' and self.rd != 'option1':
            naklady = 'naklady'
        elif self.size == 'średni' and self.rd != 'option1':
            naklady = 'nakladys'
        elif self.size == 'mały':
            naklady = 'nakladyma'
        else:
            naklady = 'nakladym'
        if self.currency == 'EURO':
            self.value *= cena
        db = get_db()
        cur = db.execute(
            'select * from gminy where {} <= {} and wojewodztwo = "{}"'.format(naklady, self.value, 'lubuskie'))
        results = cur.fetchall()
        lubuskie = {}
        for i in range(len(results)):
            lubuskie[results[i]['gmina']] = results[i]['powiat']
        if self.currency == 'EURO':
            self.value /= cena
        return lubuskie

    def wielkopolskie(self):
        if self.rd == 'option1' and self.size != 'mikro':
            naklady = 'nakladybr'
        elif self.size == 'duży' and self.rd != 'option1':
            naklady = 'naklady'
        elif self.size == 'średni' and self.rd != 'option1':
            naklady = 'nakladys'
        elif self.size == 'mały':
            naklady = 'nakladyma'
        else:
            naklady = 'nakladym'
        if self.currency == 'EURO':
            self.value *= cena
        db = get_db()
        cur = db.execute('select * from gminy where {} <= {} and wojewodztwo = "{}"'.format(
            naklady, self.value, 'wielkopolskie'))
        results = cur.fetchall()
        wielkopolskie = {}
        for i in range(len(results)):
            wielkopolskie[results[i]['gmina']] = results[i]['powiat']
        if self.currency == 'EURO':
            self.value /= cena
        return wielkopolskie

    def zachodniopomorskie(self):
        if self.rd == 'option1' and self.size != 'mikro':
            naklady = 'nakladybr'
        elif self.size == 'duży' and self.rd != 'option1':
            naklady = 'naklady'
        elif self.size == 'średni' and self.rd != 'option1':
            naklady = 'nakladys'
        elif self.size == 'mały':
            naklady = 'nakladyma'
        else:
            naklady = 'nakladym'
        if self.currency == 'EURO':
            self.value *= cena
        db = get_db()
        cur = db.execute('select * from gminy where {} <= {} and wojewodztwo = "{}"'.format(
            naklady, self.value, 'zachodniopomorskie'))
        results = cur.fetchall()
        zachodniopomorskie = {}
        for i in range(len(results)):
            zachodniopomorskie[results[i]['gmina']] = results[i]['powiat']
        if self.currency == 'EURO':
            self.value /= cena
        return zachodniopomorskie

    def gnl(self):
        db = get_db()
        cur = db.execute(
            'select * from gminy where wojewodztwo = "{}"'.format('lubuskie'))
        results = cur.fetchall()
        gminyl = {}
        if self.rd == 'option1' and self.size != 'mikro':
            for i in range(len(results)):
                gminyl[results[i]['gmina']] = results[i]['nakladybr']
        elif self.size == 'duży' and self.rd != 'option1':
            for i in range(len(results)):
                gminyl[results[i]['gmina']] = results[i]['naklady']
        elif self.size == 'średni' and self.rd != 'option1':
            for i in range(len(results)):
                gminyl[results[i]['gmina']] = results[i]['nakladys']
        elif self.size == 'mały':
            for i in range(len(results)):
                gminyl[results[i]['gmina']] = results[i]['nakladyma']
        else:
            for i in range(len(results)):
                gminyl[results[i]['gmina']] = results[i]['nakladym']
        return gminyl

    def gnw(self):
        db = get_db()
        cur = db.execute(
            'select * from gminy where wojewodztwo = "{}"'.format('wielkopolskie'))
        results = cur.fetchall()
        gminyw = {}
        if self.rd == 'option1' and self.size != 'mikro':
            for i in range(len(results)):
                gminyw[results[i]['gmina']] = results[i]['nakladybr']
        elif self.size == 'duży' and self.rd != 'option1':
            for i in range(len(results)):
                gminyw[results[i]['gmina']] = results[i]['naklady']
        elif self.size == 'średni' and self.rd != 'option1':
            for i in range(len(results)):
                gminyw[results[i]['gmina']] = results[i]['nakladys']
        elif self.size == 'mały':
            for i in range(len(results)):
                gminyw[results[i]['gmina']] = results[i]['nakladyma']
        else:
            for i in range(len(results)):
                gminyw[results[i]['gmina']] = results[i]['nakladym']
        return gminyw

    def gnz(self):
        db = get_db()
        cur = db.execute(
            'select * from gminy where wojewodztwo = "{}"'.format('zachodniopomorskie'))
        results = cur.fetchall()
        gminyz = {}
        if self.rd == 'option1' and self.size != 'mikro':
            for i in range(len(results)):
                gminyz[results[i]['gmina']] = results[i]['nakladybr']
        elif self.size == 'duży' and self.rd != 'option1':
            for i in range(len(results)):
                gminyz[results[i]['gmina']] = results[i]['naklady']
        elif self.size == 'średni' and self.rd != 'option1':
            for i in range(len(results)):
                gminyz[results[i]['gmina']] = results[i]['nakladys']
        elif self.size == 'mały':
            for i in range(len(results)):
                gminyz[results[i]['gmina']] = results[i]['nakladyma']
        else:
            for i in range(len(results)):
                gminyz[results[i]['gmina']] = results[i]['nakladym']
        return gminyz


class Fee:

    def __init__(self, expenditures, jobs, size, area, infrastructure):
        self.expenditures = expenditures
        self.jobs = jobs
        self.size = size
        self.area = area
        self.infrastructure = infrastructure

    def xw(self):
        if 10000000 > self.expenditures > 0:
            xw = 0.2
        elif 50000000 >= self.expenditures >= 10000000:
            xw = 0.07
        elif self.expenditures > 50000000:
            xw = 0.02
        else:
            xw = 0
        return float(xw)

    def xp(self):
        if 10000 > self.area > 0:
            xp = 0.005
        elif 50000 >= self.area >= 10000:
            xp = 0.02
        elif self.area > 50000:
            xp = 0.01
        else:
            xp = 0
        return xp

    def xz(self):
        if 50 > self.jobs > 0:
            xz = 0.2
        elif 250 >= self.jobs >= 50:
            xz = 0.15
        elif self.jobs > 250:
            xz = 0.1
        else:
            xz = 0
        return xz

    def xi(self):
        if self.infrastructure == 'option1':
            xi = 0.1
        else:
            xi = 0
        return xi

    def xmsp(self):
        if self.size == 'duży':
            xmsp = 1
        elif self.size == 'średni':
            xmsp = 0.9
        elif self.size == 'mały':
            xmsp = 0.8
        else:
            xmsp = 0.7
        return xmsp


cena = kurs()
cena = float(cena)
cena = float(round(cena, 2))
date = data()


@app.route('/', methods=['GET', 'POST'])
def index():
    specialist = randint(1, 4)
    back = True
    return render_template('index.html', specialist=specialist, back=back)


@app.route('/pomoc', methods=['GET', 'POST'])
def pomoc():
    if request.method == 'GET':
        specialist = randint(1, 4)
        return render_template('indexpp.html', date=date, cena=cena, specialist=specialist)
    else:
        waluta = request.form['waluta']
        region = request.form['region']
        size = request.form['size']
        value = float(request.form['value'])
        value = value * 1000000
        intensity = 0
        pp = 0
        wynik = Kalkulator(waluta=waluta, value=value, size=size,
                           region=region, intensity=intensity, pp=pp)
        dic = wynik.criteria()
        dicn = wynik.gn()
        result = defaultdict(list)
        for k, v in sorted(dic.items()):
            result[v].append(k)

        intensity = wynik.intensity2()
        wynik.intensity = intensity
        if waluta == 'PLN':
            wynik.value /= cena
        else:
            pass
        pp = wynik.cur()
        notification = wynik.notify()
        if waluta == 'PLN':
            wynik.value *= cena
            pp *= cena
        else:
            pass
        if waluta == 'EURO':
            przelicznik = pp * cena
            currency = 'PLN'
        else:
            przelicznik = pp / cena
            currency = 'EURO'
        value = '{:,}'.format(int(round(wynik.value, 2))).replace(',', ' ')
        pp = '{:,}'.format(int(round(pp, 2))).replace(',', ' ')
        przelicznik = '{:,}'.format(
            int(round(przelicznik, 2))).replace(',', ' ')
        wynik.value = value
        wynik.pp = pp
        specialist = randint(1, 4)
        return render_template('resultpp.html', notification=notification, dicn=dicn,
                               przelicznik=przelicznik, cena=cena, result=result, dic=dic,
                               waluta=waluta, currency=currency, date=date, specialist=specialist,
                               wynik=Kalkulator(waluta=waluta, value=value, size=size, region=region,
                                                intensity=intensity, pp=pp))


@app.route('/lokalizacje', methods=['GET', 'POST'])
def lokalizacje():
    specialist = randint(1, 4)
    if request.method == 'GET':
        rd = None
        currency = None
        value = None
        specialist = randint(1, 4)
        return render_template('indexlok.html', cena=cena, date=date, rd=rd, currency=currency, value=value,
                               specialist=specialist)
    else:
        currency = request.form['currency']
        value = float(request.form['value'])
        value = value * 1000000
        size = request.form['size']
        rd = request.form['options']
        places = Where(currency=currency, value=value, size=size, rd=rd)

        lubuskie = places.lubuskie()
        wielkopolskie = places.wielkopolskie()
        zachodniopomorskie = places.zachodniopomorskie()

        result = defaultdict(list)
        for k, v in sorted(lubuskie.items()):
            result[v].append(k)

        resultw = defaultdict(list)
        for k, v in sorted(wielkopolskie.items()):
            resultw[v].append(k)

        resultz = defaultdict(list)
        for k, v in sorted(zachodniopomorskie.items()):
            resultz[v].append(k)

        value = '{:,}'.format(int(round(places.value, 2))).replace(',', ' ')

        zach = places.gnz()
        lub = places.gnl()
        wlkp = places.gnw()

        return render_template('resultslok.html', result=result, resultw=resultw, resultz=resultz, rd=rd, value=value,
                               currency=places.currency, zach=zach, size=size, lub=lub, wlkp=wlkp, date=date, cena=cena,
                               specialist=specialist)


@app.route('/naklady', methods=['GET', 'POST'])
def naklady():
    specialist = randint(1, 4)
    if request.method == 'GET':
        db = get_db()
        lubuskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'lubuskie'")
        lubuskie_powiaty = lubuskie_cur.fetchall()

        wielkopolskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'wielkopolskie'")
        wielkopolskie_powiaty = wielkopolskie_cur.fetchall()

        zachodniopomorskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'zachodniopomorskie'")
        zachodniopomorskie_powiaty = zachodniopomorskie_cur.fetchall()

        return render_template('indexnak.html', lubuskie_powiaty=lubuskie_powiaty, wielkopolskie_powiaty=wielkopolskie_powiaty,
                               zachodniopomorskie_powiaty=zachodniopomorskie_powiaty, specialist=specialist)

    else:
        db = get_db()
        powiatl = request.form['powiatl']
        powiatw = request.form['powiatw']
        powiatz = request.form['powiatz']

        gminyl_cur = db.execute(
            'select * from gminy where powiat = ?', [powiatl])
        gminyl = gminyl_cur.fetchall()

        gminyw_cur = db.execute(
            'select * from gminy where powiat = ?', [powiatw])
        gminyw = gminyw_cur.fetchall()

        gminyz_cur = db.execute(
            'select * from gminy where powiat = ?', [powiatz])
        gminyz = gminyz_cur.fetchall()

        lubuskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'lubuskie'")
        lubuskie_powiaty = lubuskie_cur.fetchall()

        wielkopolskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'wielkopolskie'")
        wielkopolskie_powiaty = wielkopolskie_cur.fetchall()

        zachodniopomorskie_cur = db.execute(
            "SELECT DISTINCT powiat FROM gminy where wojewodztwo = 'zachodniopomorskie'")
        zachodniopomorskie_powiaty = zachodniopomorskie_cur.fetchall()

        return render_template('indexnak.html', powiatl=powiatl, powiatw=powiatw, powiatz=powiatz, gminyl=gminyl,
                               gminyw=gminyw, gminyz=gminyz, lubuskie_powiaty=lubuskie_powiaty,
                               wielkopolskie_powiaty=wielkopolskie_powiaty,
                               zachodniopomorskie_powiaty=zachodniopomorskie_powiaty, specialist=specialist)


@app.route('/oplata', methods=['GET', 'POST'])
def fee():
    specialist = randint(1, 4)
    if request.method == 'GET':
        return render_template('indexopl.html', date=date, cena=cena, specialist=specialist)
    else:
        currency = request.form['currency']
        expenditures = float(request.form['expenditures'])
        if currency == 'EURO':
            expenditures *= cena
        else:
            pass
        jobs = int(request.form['jobs'])
        size = request.form['size']
        area = int(request.form['area'])
        time = int(request.form['time'])
        infrastructure = request.form['options']
        payment = Fee(expenditures=expenditures, jobs=jobs,
                      size=size, area=area, infrastructure=infrastructure)
        xw = payment.xw()
        xp = payment.xp()
        xz = payment.xz()
        xi = payment.xi()
        xmsp = payment.xmsp()
        months = time * 12
        xn = 0.05 * (xw + xp + xz + xi) * xmsp
        pay = xn * expenditures / months
        pay = round(pay, 2)
        if currency == 'EURO':
            expenditures /= cena
            pay /= cena
            przelicznik = pay * cena
        else:
            przelicznik = pay / cena
        przelicznik = float(round(przelicznik, 2))
        expenditures = int(expenditures)

        return render_template('resultopl.html', pay=pay, time=time, specialist=specialist, date=date, cena=cena,
                               expenditures=expenditures, area=area, currency=currency, jobs=jobs, size=size,
                               infrastructure=infrastructure, months=months, przelicznik=przelicznik)


if __name__ == '__main__':
    app.run()

