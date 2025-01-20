from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Kunci untuk flash messages

# Inisialisasi keranjang belanja
@app.before_request
def init_cart():
    if 'keranjang' not in session:
        session['keranjang'] = []

# Koneksi ke database
def get_db_connection():
    conn = sqlite3.connect('kasir.db')
    conn.row_factory = sqlite3.Row
    return conn

# Buat tabel produk jika belum ada
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY,
            nama TEXT,
            harga_pcs REAL,
            harga_pack REAL,
            stok INTEGER
        )
    ''')
    conn.close()

# Halaman utama
@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM produk').fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Menambahkan produk
@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    harga_pcs = request.form['harga_pcs']
    harga_pack = request.form['harga_pack']
    stok = request.form['stok']
    if name and harga_pcs and harga_pack and stok:
        conn = get_db_connection()
        conn.execute('INSERT INTO produk (nama, harga_pcs, harga_pack, stok) VALUES (?, ?, ?, ?)', (name, harga_pcs, harga_pack, stok))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

# Mengedit produk
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM produk WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        harga_pcs = request.form['harga_pcs']
        harga_pack = request.form['harga_pack']
        stok = request.form['stok']
        conn.execute('UPDATE produk SET nama = ?, harga_pcs = ?, harga_pack = ?, stok = ? WHERE id = ?', (name, harga_pcs, harga_pack, stok, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    conn.close()
    return render_template('edit.html', product=product)

# Menambahkan barang ke keranjang
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    unit = request.form['unit']  # pcs atau pack

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM produk WHERE id = ?', (product_id,)).fetchone()
    
    if product:
        item = {
            'id': product['id'],
            'nama': product['nama'],
            'harga': product['harga_pcs'] if unit == 'pcs' else product['harga_pack'],
            'jumlah': quantity,
            'satuan': unit
        }
        session['keranjang'].append(item)
        session.modified = True  # Mark session as modified
        flash('Barang berhasil ditambahkan ke keranjang.', 'success')
    
    conn.close()
    return redirect(url_for('index'))

# Menghapus barang dari keranjang
@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    session['keranjang'] = [item for item in session['keranjang'] if item['id'] != item_id]
    session.modified = True  # Mark session as modified
    flash('Barang berhasil dihapus dari keranjang.', 'success')
    return redirect(url_for('cart'))

# Menampilkan keranjang
@app.route('/cart')
def cart():
    total = sum(item['harga'] * item['jumlah'] for item in session['keranjang'])
    return render_template('cart.html', keranjang=session['keranjang'], total=total)

# Menyelesaikan transaksi
@app.route('/checkout', methods=['POST'])
def checkout():
    # Di sini Anda dapat menambahkan logika untuk menyimpan transaksi ke database jika diperlukan
    session['keranjang'] = []  # Kosongkan keranjang setelah checkout
    flash('Transaksi berhasil! Silakan cetak struk.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Inisialisasi database
    app.run(debug=True)