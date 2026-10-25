import os
import random
from flask import Flask, render_template, request, session, flash, redirect, url_for
import mysql.connector
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = "warehouse_secret_key"

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# --- 1. LOGIN & AUTH ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('owner_dashboard') if session.get('role') == 'owner' else url_for('pos'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        selected_role = request.form.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            if user['role'] == 'pending':
                flash("Your account is pending Owner approval.", "error")
            elif user['role'] == 'suspended':
                flash("Your account has been suspended by the Owner.", "error")
            elif user['role'] != selected_role:
                flash(f"Access Denied. You are not registered as an {selected_role.capitalize()}.", "error")
            else:
                session['logged_in'] = True
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('owner_dashboard') if user['role'] == 'owner' else url_for('pos'))
        else:
            flash("Invalid credentials", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- 2. FORGOT PASSWORD & OTP ---
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND phone_number = %s", (username, phone))
        user = cursor.fetchone()
        
        if user:
            # Generate a 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Save OTP to database
            cursor.execute("UPDATE users SET reset_otp = %s WHERE id = %s", (otp, user['id']))
            conn.commit()
            
            # In a real app, you would send an SMS here. 
            # For this demo, we will flash it to the screen.
            flash(f"DEMO MODE: Your OTP is {otp}. (In real life, this would be sent via SMS to {phone})", "success")
            return redirect(url_for('reset_password', username=username))
        else:
            flash("No account found with that username and phone number.", "error")
            
        cursor.close()
        conn.close()
        
    return render_template('forgot_password.html')

@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        otp_entered = request.form['otp']
        new_password = request.form['new_password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND reset_otp = %s", (username, otp_entered))
        user = cursor.fetchone()
        
        if user:
            # Update password and clear the OTP
            cursor.execute("UPDATE users SET password = %s, reset_otp = NULL WHERE id = %s", (new_password, user['id']))
            conn.commit()
            flash("Password reset successfully! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid OTP code. Please try again.", "error")
            
        cursor.close()
        conn.close()
        
    return render_template('reset_password.html', username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already exists!", "error")
        else:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'pending')", (username, password))
            conn.commit()
            flash("Registration successful! Please wait for Owner approval.", "success")
        cursor.close()
        conn.close()
    return render_template('register.html')

# --- 3. OWNER DASHBOARD ---
@app.route('/owner_dashboard')
def owner_dashboard():
    if session.get('role') != 'owner': return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT SUM(total_amount) as total FROM sales")
    result = cursor.fetchone()
    total_revenue = result['total'] if result['total'] else 0.00
    
    cursor.execute("SELECT * FROM inventory")
    inventory = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'pending'")
    pending = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('owner_dashboard.html', revenue=total_revenue, inventory=inventory, pending=pending)

# --- 4. OWNER ACTIONS ---
@app.route('/approve_employee/<int:user_id>')
def approve_employee(user_id):
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'employee' WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Employee approved!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/add_item', methods=['POST'])
def add_item():
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO inventory (item_name, price_per_kg, quantity_kg) VALUES (%s, %s, %s)", 
                       (request.form['item_name'], request.form['price'], request.form['quantity']))
        conn.commit()
        flash("Item added successfully!", "success")
    except mysql.connector.Error:
        flash("Item already exists!", "error")
    cursor.close()
    conn.close()
    return redirect(url_for('owner_dashboard'))

@app.route('/update_price/<int:item_id>', methods=['POST'])
def update_price(item_id):
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET price_per_kg = %s WHERE id = %s", (request.form['new_price'], item_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Price updated!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Item deleted.", "success")
    return redirect(url_for('owner_dashboard'))

# --- 5. STAFF MANAGEMENT ---
@app.route('/manage_staff')
def manage_staff():
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role IN ('employee', 'suspended')")
    staff = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_staff.html', staff=staff)

@app.route('/toggle_staff/<int:user_id>/<string:new_role>')
def toggle_staff(user_id, new_role):
    if session.get('role') != 'owner': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f"Employee status updated to {new_role}.", "success")
    return redirect(url_for('manage_staff'))

# --- 6. REPORTS ---
@app.route('/reports')
def reports():
    if session.get('role') != 'owner': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT item_name, SUM(quantity_sold) as total_qty, SUM(quantity_sold * price_at_sale) as total_revenue FROM sale_items GROUP BY item_name ORDER BY total_qty DESC")
    item_reports = cursor.fetchall()
    
    item_names = [row['item_name'] for row in item_reports]
    item_quantities = [int(row['total_qty']) for row in item_reports]
    
    cursor.execute("SELECT employee_username, COUNT(id) as total_sales, SUM(total_amount) as total_revenue FROM sales GROUP BY employee_username ORDER BY total_revenue DESC")
    employee_reports = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('reports.html', item_reports=item_reports, employee_reports=employee_reports, item_names=item_names, item_quantities=item_quantities)

# --- 7. POS & CHECKOUT ---
@app.route('/pos', methods=['GET', 'POST'])
def pos():
    if session.get('role') != 'employee': return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    show_qr = False
    total_bill = 0

    if request.method == 'POST':
        cust_name = request.form['cust_name']
        cust_phone = request.form['cust_phone']
        items_sold = []

        for key, value in request.form.items():
            if key.startswith('qty_') and value.strip() != '' and int(value) > 0:
                item_name = key.replace('qty_', '')
                qty = int(value)
                
                cursor.execute("SELECT price_per_kg, quantity_kg FROM inventory WHERE item_name = %s", (item_name,))
                item = cursor.fetchone()
                
                if item and item['quantity_kg'] >= qty:
                    total_bill += item['price_per_kg'] * qty
                    items_sold.append({'name': item_name, 'qty': qty, 'price': item['price_per_kg']})
                else:
                    flash(f"Not enough stock for {item_name}!", "error")
                    return redirect(url_for('pos'))

        if items_sold:
            today = date.today()
            cursor.execute("INSERT INTO sales (employee_username, customer_name, customer_phone, total_amount, date) VALUES (%s, %s, %s, %s, %s)",
                           (session['username'], cust_name, cust_phone, total_bill, today))
            sale_id = cursor.lastrowid

            for item in items_sold:
                cursor.execute("INSERT INTO sale_items (sale_id, item_name, quantity_sold, price_at_sale) VALUES (%s, %s, %s, %s)",
                               (sale_id, item['name'], item['qty'], item['price']))
                cursor.execute("UPDATE inventory SET quantity_kg = quantity_kg - %s WHERE item_name = %s",
                               (item['qty'], item['name']))
            
            conn.commit()
            show_qr = True
            flash(f"Transaction Complete! Total Amount: ₹{total_bill}", "success")
        else:
            flash("Please enter a quantity for at least one item to checkout!", "error")

    cursor.execute("SELECT * FROM inventory")
    inventory = cursor.fetchall()
    
    today = date.today()
    cursor.execute("SELECT SUM(total_amount) as today_total FROM sales WHERE employee_username = %s AND date = %s", (session['username'], today))
    today_total = cursor.fetchone()['today_total'] or 0.00

    cursor.close()
    conn.close()
    return render_template('pos.html', inventory=inventory, show_qr=show_qr, total_bill=total_bill, today_total=today_total)

# --- 8. HISTORY & RECEIPT ---
@app.route('/history')
def history():
    if not session.get('logged_in'): return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if session.get('role') == 'employee':
        cursor.execute("SELECT * FROM sales WHERE employee_username = %s ORDER BY id ASC", (session['username'],))
    else:
        cursor.execute("SELECT * FROM sales ORDER BY id ASC")
    
    sales = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('history.html', sales=sales)

@app.route('/receipt/<int:sale_id>')
def receipt(sale_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM sales WHERE id = %s", (sale_id,))
    sale = cursor.fetchone()
    
    cursor.execute("SELECT * FROM sale_items WHERE sale_id = %s", (sale_id,))
    items = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('receipt.html', sale=sale, items=items)

if __name__ == '__main__':
    app.run(debug=True)