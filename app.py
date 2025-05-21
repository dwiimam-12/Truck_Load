import os

from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secretkey'

GUDANG_LIST = [
    'Gd PF I', 'Gd PF II', 'Gd 09B#650', 'Gd 09A#650', 'Gd 02#650',
    'Gd NPK II', 'Gd Curring PF I', 'Gd Curring PF II', 'Gd PA',
    'Gd Dome', 'Gd Sulphur', 'Gd 50.000', 'Gd Puri 1', 'Gd Puri 2',
    'Gd P.Rock PJA', 'Gd Sulphur PJA', 'Gd Gypsum PJA', 'Gd BS Belerang',
    'Gd BS ZA', 'Gd BS Urea'
]

SHIFT_MAP = {
    'Shift 1': '07.01 - 14.00',
    'Shift 2': '14.01 - 22.00',
    'Shift 3': '22.01 - 07.00'
}

def init_db():
    conn = sqlite3.connect('penimbangan.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT,
        kapal TEXT,
        plat TEXT,
        tonase REAL,
        shift TEXT,
        gudang TEXT,
        jam TEXT
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('penimbangan.db')
    df = pd.read_sql_query("SELECT * FROM data", conn)
    conn.close()
    rekap = df.groupby(['tanggal', 'shift', 'gudang'])['tonase'].sum().reset_index()
    return render_template('index.html', gudangs=GUDANG_LIST, shifts=SHIFT_MAP, data=df.to_dict('records'), rekap=rekap.to_dict('records'))

@app.route('/submit', methods=['POST'])
def submit():
    data = {
        'tanggal': request.form['tanggal'],
        'kapal': request.form['kapal'],
        'plat': request.form['plat'],
        'tonase': float(request.form['tonase']),
        'shift': request.form['shift'],
        'gudang': request.form['gudang'],
        'jam': datetime.now().strftime("%H:%M:%S")
    }
    conn = sqlite3.connect('penimbangan.db')
    c = conn.cursor()
    c.execute("INSERT INTO data (tanggal, kapal, plat, tonase, shift, gudang, jam) VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (data['tanggal'], data['kapal'], data['plat'], data['tonase'], data['shift'], data['gudang'], data['jam']))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/export')
def export():
    conn = sqlite3.connect('penimbangan.db')
    df = pd.read_sql_query("SELECT * FROM data", conn)
    conn.close()
    df.to_excel("rekap_penimbangan.xlsx", index=False)
    return send_file("rekap_penimbangan.xlsx", as_attachment=True)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


