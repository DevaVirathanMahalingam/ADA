from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super secret key"

# Initialize database
def init_db():
    conn = sqlite3.connect('ada_transport.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT
        )''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            datetime TEXT,
            material_name TEXT,
            vehicle_number TEXT,
            driver_name TEXT,
            material_cost REAL,
            transport_cost REAL,
            from_location TEXT,
            to_location TEXT,
            paid_amount REAL,
            total_amount REAL,
            remaining_amount REAL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == "sam" and password == "ada":
        flash('Login successful', 'success')
        return redirect(url_for('data_entry'))
    else:
        flash('Invalid credentials', 'danger')
        return redirect(url_for('index'))

@app.route('/data_entry', methods=['GET', 'POST'])
def data_entry():
    if request.method == 'POST':
        client_name = request.form['client_name']
        material_name = request.form['material_name']
        vehicle_number = request.form['vehicle_number']
        driver_name = request.form['driver_name']
        material_cost = float(request.form['material_cost'])
        transport_cost = float(request.form['transport_cost'])
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        paid_amount = float(request.form['paid_amount'])
        total_amount = material_cost + transport_cost
        remaining_amount = total_amount - paid_amount

        conn = sqlite3.connect('ada_transport.db')
        c = conn.cursor()
        
        c.execute("INSERT OR IGNORE INTO clients (name) VALUES (?)", (client_name,))
        c.execute("SELECT id FROM clients WHERE name=?", (client_name,))
        client_id = c.fetchone()[0]

        c.execute('''
            INSERT INTO records (
                client_id, datetime, material_name, vehicle_number, driver_name, material_cost, transport_cost, from_location, to_location, paid_amount, total_amount, remaining_amount
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
                client_id, datetime.now(), material_name, vehicle_number, driver_name, material_cost, transport_cost, from_location, to_location, paid_amount, total_amount, remaining_amount
            ))
        
        conn.commit()
        conn.close()
        flash('Data saved successfully', 'success')
        return redirect(url_for('client_dashboard', client_name=client_name))
    
    return render_template('data_entry.html')

# Client dashboard with totals
@app.route('/dashboard/<client_name>')
def client_dashboard(client_name):
    conn = sqlite3.connect('ada_transport.db')
    c = conn.cursor()
    
    # Get the client ID
    c.execute("SELECT id FROM clients WHERE name=?", (client_name,))
    client = c.fetchone()
    
    if client is None:
        flash(f'Client {client_name} not found', 'danger')
        return redirect(url_for('index'))
    
    client_id = client[0]
    
    # Fetch all records for this client
    c.execute("SELECT * FROM records WHERE client_id=?", (client_id,))
    records = c.fetchall()
    
    # Calculate totals
    c.execute("""
        SELECT SUM(material_cost), SUM(transport_cost), SUM(total_amount), SUM(remaining_amount)
        FROM records WHERE client_id=?
    """, (client_id,))
    totals = c.fetchone()
    material_total, transport_total, total_amount, remaining_total = totals
    
    conn.close()
    return render_template('/dashboard.html', 
                           client_name=client_name, 
                           records=records, 
                           material_total=material_total,
                           transport_total=transport_total, 
                           total_amount=total_amount, 
                           remaining_total=remaining_total)

# Route to clear all records for a specific client
@app.route('/clear_client_data/<client_name>', methods=['POST'])
def clear_client_data(client_name):
    conn = sqlite3.connect('ada_transport.db')
    c = conn.cursor()

    # Get client ID
    c.execute("SELECT id FROM clients WHERE name=?", (client_name,))
    client = c.fetchone()
    
    if client is not None:
        client_id = client[0]
        # Delete all records for this client
        c.execute("DELETE FROM records WHERE client_id=?", (client_id,))
        conn.commit()
        flash(f'All data for {client_name} cleared successfully', 'success')
    else:
        flash(f'Client {client_name} not found', 'danger')

    conn.close()
    return redirect(url_for('client_dashboard', client_name=client_name))

# Route to clear all data (both clients and records)
@app.route('/clear_data', methods=['POST'])
def clear_data():
    conn = sqlite3.connect('ada_transport.db')
    c = conn.cursor()
    c.execute("DELETE FROM records")
    c.execute("DELETE FROM clients")
    conn.commit()
    conn.close()
    flash('All data cleared successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
