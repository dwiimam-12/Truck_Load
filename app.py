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

EMKL_LIST = ['Petro Karya Trans', 'Trans Cipta Selaras', 'PCS']


def init_db():
    conn = sqlite3.connect('penimbangan.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            kapal TEXT,
            plat TEXT,
            tonase REAL,
            shift TEXT,
            gudang TEXT,
            jam TEXT,
            emkl TEXT
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('penimbangan.db')
    df = pd.read_sql_query("SELECT * FROM data", conn)
    conn.close()

    # Rekap per tanggal, shift, dan gudang
    rekap = df.groupby(['tanggal', 'shift', 'gudang'])['tonase'].sum().reset_index()

    # Rekap per kapal dan EMKL
    rekap_emkl = df.groupby(['kapal', 'emkl'])['tonase'].sum().reset_index()

    return render_template(
        'index.html',
        gudangs=GUDANG_LIST,
        shifts=SHIFT_MAP,
        emkls=EMKL_LIST,
        data=df.to_dict('records'),
        rekap=rekap.to_dict('records'),
        rekap_emkl=rekap_emkl.to_dict('records')
    )


@app.route('/submit', methods=['POST'])
def submit():
    if 'user' not in session:
        return redirect(url_for('login'))

    data = {
        'tanggal': request.form['tanggal'],
        'kapal': request.form['kapal'],
        'plat': request.form['plat'],
        'tonase': float(request.form['tonase']),
        'shift': request.form['shift'],
        'gudang': request.form['gudang'],
        'jam': datetime.now().strftime("%H:%M:%S"),
        'emkl': request.form['emkl']
    }

    conn = sqlite3.connect('penimbangan.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO data (tanggal, kapal, plat, tonase, shift, gudang, jam, emkl) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['tanggal'], data['kapal'], data['plat'], data['tonase'],
          data['shift'], data['gudang'], data['jam'], data['emkl']))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('penimbangan.db')
    c = conn.cursor()

    if request.method == 'POST':
        c.execute('''
            UPDATE data SET tanggal=?, kapal=?, plat=?, tonase=?, shift=?, gudang=?, emkl=? WHERE id=?
        ''', (
            request.form['tanggal'],
            request.form['kapal'],
            request.form['plat'],
            float(request.form['tonase']),
            request.form['shift'],
            request.form['gudang'],
            request.form['emkl'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    row = c.execute('SELECT * FROM data WHERE id=?', (id,)).fetchone()
    conn.close()

    if row:
        keys = ['id', 'tanggal', 'kapal', 'plat', 'tonase', 'shift', 'gudang', 'jam', 'emkl']
        data = dict(zip(keys, row))
        return render_template('edit.html', data=data, gudangs=GUDANG_LIST, shifts=SHIFT_MAP, emkls=EMKL_LIST)
    else:
        return "Data not found", 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('home'))
        else:
            error = 'Username atau password salah!'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/export')
def export():
    if 'user' not in session:
        return redirect(url_for('login'))

    kapal_filter = request.args.get('kapal')

    conn = sqlite3.connect('penimbangan.db')
    df = pd.read_sql_query("SELECT * FROM data", conn)
    conn.close()

    if kapal_filter:
        df = df[df['kapal'].str.contains(kapal_filter, case=False, na=False)]

    filename = f"rekap_penimbangan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)

    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
