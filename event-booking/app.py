from flask import Flask, render_template, request, redirect, session, flash, url_for
from db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random

app = Flask(__name__)
app.secret_key = "event_secret"

# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            return redirect('/admin/dashboard' if user['role'] == 'admin' else '/dashboard')

        flash("Invalid email or password", "error")

    return render_template('login.html')


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,'user')",
            (
                request.form['name'],
                request.form['email'],
                generate_password_hash(request.form['password'])
            )
        )
        conn.commit()
        conn.close()

        flash("Registration successful", "success")
        return redirect('/login')

    return render_template('register.html')


# ================= USER DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')


# ================= EVENTS =================
@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events ORDER BY event_date")
    events = cursor.fetchall()
    conn.close()

    return render_template('event.html', events=events)


# ================= BOOK EVENT =================
@app.route('/book/<int:event_id>')
def book_event(event_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT seats FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()

    if event and event['seats'] > 0:
        year = datetime.datetime.now().year
        rand = random.randint(100000, 999999)
        booking_id = f"BK-{year}-{rand}"

        cursor.execute("""
            INSERT INTO bookings (booking_id, user_id, event_id, booking_date, status)
            VALUES (%s, %s, %s, CURDATE(), 'Booked')
        """, (booking_id, session['user_id'], event_id))

        cursor.execute(
            "UPDATE events SET seats = seats - 1 WHERE id=%s",
            (event_id,)
        )

        conn.commit()
        flash(f"🎉 Event booked! Booking ID: {booking_id}", "success")

    else:
        flash("❌ Event sold out!", "error")

    conn.close()
    return redirect('/events')



# ================= MY BOOKINGS =================
@app.route('/mybookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            b.booking_id,
            e.title,
            e.event_date,
            e.location,
            b.booking_date,
            b.status
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """, (session['user_id'],))

    bookings = cursor.fetchall()
    return render_template('mybookings.html', bookings=bookings)



# ================= USER CANCEL =================
@app.route('/cancel-booking/<booking_id>')
def cancel_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings
        SET status = 'Cancelled'
        WHERE booking_id = %s
    """, (booking_id,))

    conn.commit()
    return redirect('/mybookings')



# ================= ADMIN DASHBOARD =================
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) total FROM events")
    total_events = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) total FROM users")
    total_users = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) total FROM bookings")
    total_bookings = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) total FROM bookings WHERE status='Booked'")
    active_bookings = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) total FROM bookings WHERE status='Cancelled'")
    cancelled_bookings = cursor.fetchone()['total']

    cursor.execute("""
        SELECT e.title, COUNT(b.id) count
        FROM events e LEFT JOIN bookings b ON e.id=b.event_id
        GROUP BY e.id
    """)
    chart = cursor.fetchall()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_events=total_events,
        total_users=total_users,
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        cancelled_bookings=cancelled_bookings,
        event_labels=[c['title'] for c in chart],
        booking_counts=[c['count'] for c in chart]
    )


# ================= ADMIN EVENTS =================
@app.route('/admin/events')
def admin_events():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
    events = cursor.fetchall()
    conn.close()

    return render_template('admin_events.html', events=events)


# ================= ADMIN EDIT EVENT =================
@app.route('/admin/edit-event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("""
            UPDATE events SET title=%s,event_date=%s,location=%s,price=%s,seats=%s
            WHERE id=%s
        """, (
            request.form['title'],
            request.form['event_date'],
            request.form['location'],
            request.form['price'],
            request.form['seats'],
            event_id
        ))
        conn.commit()
        conn.close()
        flash("Event updated", "success")
        return redirect('/admin/events')

    cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()
    conn.close()

    return render_template('edit_event.html', event=event)


# ================= ADMIN DELETE EVENT =================
@app.route('/admin/delete-event/<int:event_id>')
def delete_event(event_id):
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE event_id=%s", (event_id,))
    cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
    conn.commit()
    conn.close()

    flash("Event deleted", "success")
    return redirect('/admin/events')

# ================= ADMIN BOOKINGS =================

@app.route('/admin/bookings')
def admin_bookings():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            b.booking_id,
            u.name AS user_name,
            e.title AS event_title,
            b.booking_date,
            b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN events e ON b.event_id = e.id
        ORDER BY b.booking_date DESC
    """)

    bookings = cursor.fetchall()
    conn.close()

    return render_template('admin_bookings.html', bookings=bookings)
# ================= ADMIN ADD EVENT =================


@app.route('/admin/add-event', methods=['GET', 'POST'])
def admin_add_event():
    if session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events (title, event_date, location, price, seats)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            request.form['title'],
            request.form['event_date'],
            request.form['location'],
            request.form['price'],
            request.form['seats']
        ))

        conn.commit()
        conn.close()

        flash("Event added successfully", "success")
        return redirect('/admin/events')

    return render_template('admin_add_event.html')

# ================= ADMIN CANCEL BOOKING =================
@app.route('/admin/cancel-booking/<booking_id>')
def admin_cancel_booking(booking_id):
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings
        SET status='Cancelled'
        WHERE booking_id=%s
    """, (booking_id,))

    conn.commit()
    conn.close()
    return redirect('/admin/bookings')

# ================= PAYMENT =================

@app.route('/payment/<int:event_id>', methods=['GET', 'POST'])
def payment(event_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM events WHERE id=%s", (event_id,))
    event = cursor.fetchone()

    if request.method == 'POST':
        # create booking
        cursor.execute("""
            INSERT INTO bookings (user_id, event_id, booking_date, status, payment_status)
            VALUES (%s, %s, CURDATE(), 'Booked', 'Paid')
        """, (session['user_id'], event_id))

        booking_db_id = cursor.lastrowid
        booking_id = f"BK-2026-{str(booking_db_id).zfill(6)}"

        cursor.execute("""
            UPDATE bookings SET booking_id=%s WHERE id=%s
        """, (booking_id, booking_db_id))

        cursor.execute("UPDATE events SET seats = seats - 1 WHERE id=%s", (event_id,))

        conn.commit()
        conn.close()

        flash(f"🎉 Payment successful! Booking ID: {booking_id}", "success")
        return redirect('/mybookings')

    conn.close()
    return render_template('payment.html', event=event)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
