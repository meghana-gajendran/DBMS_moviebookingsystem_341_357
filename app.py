from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = 'movie_booking_secret_key_2024'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Maggie@123', 
    'database': 'MovieBookingSystem'
}

def get_db_connection():
    try:
        # Use buffered=True for safety when fetching multiple result sets or executing multiple statements
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- NEW: ADMIN REQUIRED DECORATOR ---
# Assuming User ID 1 is the Administrator (Nohara)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        # Hardcoded check for Admin: User_ID = 1. You should use a role column in a real app.
        if session.get('user_id') != 1: 
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- CORE ROUTES (Index, Movies, Shows, Bookings) - UNCHANGED ---

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed! Check your MySQL credentials."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # SOLUTION 4: Auto-refresh show dates if most are outdated
        cursor.execute("SELECT COUNT(*) as outdated_count FROM SHOWS WHERE Show_Date < CURDATE()")
        result = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_shows FROM SHOWS")
        total_shows = cursor.fetchone()['total_shows']
        
        if total_shows > 0 and result['outdated_count'] > total_shows * 0.5: 
            print("Auto-refreshing show dates...")
            cursor.execute("UPDATE SHOWS SET Show_Date = DATE_ADD(CURDATE(), INTERVAL FLOOR(RAND() * 7) DAY)")
            conn.commit()
            flash('Show dates have been automatically updated for better availability!', 'info')

        # Get featured movies
        cursor.execute("SELECT * FROM MOVIE ORDER BY Rating DESC LIMIT 3")
        featured_movies = cursor.fetchall()
        
        # Get upcoming shows
        cursor.execute("""
            SELECT s.Show_ID, m.Title, t.Name as Theatre_Name, s.Show_Date, s.Show_Time, s.Price
            FROM SHOWS s
            JOIN MOVIE m ON s.Movie_ID = m.Movie_ID
            JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
            JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
            WHERE s.Show_Date >= CURDATE()
            ORDER BY s.Show_Date, s.Show_Time
            LIMIT 6
        """)
        upcoming_shows = cursor.fetchall()
        
        # Get stats
        cursor.execute("SELECT COUNT(*) as count FROM MOVIE")
        movie_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM THEATRE")
        theatre_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM USERS")
        user_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM BOOKING")
        booking_count = cursor.fetchone()['count']
        
        stats = {
            'movie_count': movie_count,
            'theatre_count': theatre_count,
            'user_count': user_count,
            'booking_count': booking_count
        }
        
    except mysql.connector.Error as err:
        flash(f'Database error: {err}', 'error')
        featured_movies = []
        upcoming_shows = []
        stats = {}
    finally:
        cursor.close()
        conn.close()
    
    return render_template('home.html', 
                           featured_movies=featured_movies, 
                           upcoming_shows=upcoming_shows,
                           stats=stats)

@app.route('/movies')
def movies():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed!"
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM MOVIE ORDER BY Title")
        movies = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error loading movies: {err}', 'error')
        movies = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('movies.html', movies=movies)

@app.route('/movie/<int:movie_id>/shows')
def shows_by_movie(movie_id):
    conn = get_db_connection()
    if not conn:
        return "Database connection failed!"
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get movie details
        cursor.execute("SELECT * FROM MOVIE WHERE Movie_ID = %s", (movie_id,))
        movie = cursor.fetchone()
        
        # Get shows for this movie
        cursor.execute("""
            SELECT s.Show_ID, t.Name as Theatre_Name, sc.Screen_Number, 
                    s.Show_Date, s.Show_Time, s.Price,
                    sc.Total_Seats - IFNULL((
                        SELECT SUM(b.Seats_Booked) 
                        FROM BOOKING b 
                        WHERE b.Show_ID = s.Show_ID AND b.Status != 'Cancelled'
                    ), 0) as Available_Seats
            FROM SHOWS s
            JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
            JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
            WHERE s.Movie_ID = %s AND s.Show_Date >= CURDATE()
            ORDER BY s.Show_Date, s.Show_Time
        """, (movie_id,))
        shows = cursor.fetchall()
        
    except mysql.connector.Error as err:
        flash(f'Error loading shows: {err}', 'error')
        movie = None
        shows = []
    finally:
        cursor.close()
        conn.close()
    
    if not movie:
        flash('Movie not found!', 'error')
        return redirect(url_for('movies'))
    
    return render_template('shows.html', movie=movie, shows=shows)

@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(show_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('movies'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        selected_seats = request.form.getlist('seats')
        payment_mode = request.form['payment_mode']
        
        if not selected_seats:
            flash('Please select at least one seat!', 'error')
            return redirect(url_for('book_ticket', show_id=show_id))
        
        try:
            # Check if seats are still available
            placeholders = ','.join(['%s'] * len(selected_seats))
            cursor.execute(f"""
                SELECT Seat_Number FROM SEAT_RESERVATION 
                WHERE Show_ID = %s AND Seat_Number IN ({placeholders}) AND Is_Booked = TRUE
            """, [show_id] + selected_seats)
            
            booked_seats = cursor.fetchall()
            if booked_seats:
                flash(f'Some seats are already booked: {[s["Seat_Number"] for s in booked_seats]}', 'error')
                return redirect(url_for('book_ticket', show_id=show_id))
            
            # Calculate total amount
            cursor.execute("SELECT Price FROM SHOWS WHERE Show_ID = %s", (show_id,))
            show_result = cursor.fetchone()
            if not show_result:
                flash('Show not found!', 'error')
                return redirect(url_for('book_ticket', show_id=show_id))
            
            show_price = show_result['Price']
            total_amount = show_price * len(selected_seats)
            
            # Get next booking ID
            cursor.execute("SELECT IFNULL(MAX(Booking_ID), 300) + 1 as next_id FROM BOOKING")
            booking_result = cursor.fetchone()
            booking_id = booking_result['next_id']
            
            # Create booking with seat numbers
            try:
                cursor.execute("""
                    INSERT INTO BOOKING (Booking_ID, Show_ID, User_ID, Seats_Booked, Booking_Date, Total_Amount, Status, Seat_Numbers)
                    VALUES (%s, %s, %s, %s, CURDATE(), %s, 'Pending', %s)
                """, (booking_id, show_id, session['user_id'], len(selected_seats), total_amount, ','.join(selected_seats)))
            except mysql.connector.Error:
                # Fallback if Seat_Numbers column is missing (though it should exist based on DDL)
                cursor.execute("""
                    INSERT INTO BOOKING (Booking_ID, Show_ID, User_ID, Seats_Booked, Booking_Date, Total_Amount, Status)
                    VALUES (%s, %s, %s, %s, CURDATE(), %s, 'Pending')
                """, (booking_id, show_id, session['user_id'], len(selected_seats), total_amount))
            
            # Mark seats as booked
            for seat in selected_seats:
                cursor.execute("""
                    UPDATE SEAT_RESERVATION 
                    SET Is_Booked = TRUE, Booking_ID = %s 
                    WHERE Show_ID = %s AND Seat_Number = %s
                """, (booking_id, show_id, seat))
            
            # Get next payment ID
            cursor.execute("SELECT IFNULL(MAX(Payment_ID), 400) + 1 as next_payment_id FROM PAYMENT")
            payment_result = cursor.fetchone()
            payment_id = payment_result['next_payment_id']
            
            cursor.execute("""
                INSERT INTO PAYMENT (Payment_ID, Booking_ID, Amount, Payment_Mode, Payment_State)
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (payment_id, booking_id, total_amount, payment_mode))
            
            conn.commit()
            flash(f'Successfully booked seats: {", ".join(selected_seats)}! Payment is Pending.', 'success')
            return redirect(url_for('my_bookings'))
            
        except mysql.connector.Error as err:
            flash(f'Booking failed: {err}', 'error')
            conn.rollback()
            print(f"Booking error: {err}")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('book_ticket', show_id=show_id))
    
    # GET REQUEST
    try:
        # Get show details
        cursor.execute("""
            SELECT s.*, m.Title, m.Image_URL, t.Name as Theatre_Name, sc.Screen_Number, sc.Total_Seats
            FROM SHOWS s
            JOIN MOVIE m ON s.Movie_ID = m.Movie_ID
            JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
            JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
            WHERE s.Show_ID = %s
        """, (show_id,))
        show = cursor.fetchone()
        
        if not show:
            flash('Show not found!', 'error')
            return redirect(url_for('movies'))
        
        # Get seat layout
        cursor.execute("SELECT Seat_Number, Is_Booked FROM SEAT_RESERVATION WHERE Show_ID = %s ORDER BY Seat_Number", (show_id,))
        seats = cursor.fetchall()
        
        print(f"Seats found for show {show_id}: {len(seats)}")
        
        # AUTO-CREATE SEATS IF NONE EXIST (Fallback for missing InitializeSeatsForShow call)
        if not seats:
            print(f"Auto-creating {show['Total_Seats']} seats for show {show_id}")
            total_seats = show['Total_Seats']
            
            seat_values = []
            for i in range(1, total_seats + 1):
                row = chr(64 + ((i - 1) // 10 + 1))  # A, B, C, etc.
                seat_num = (i - 1) % 10 + 1
                seat_number = f"{row}{seat_num}"
                seat_values.append((show_id, seat_number, False))
            
            cursor.executemany(
                "INSERT IGNORE INTO SEAT_RESERVATION (Show_ID, Seat_Number, Is_Booked) VALUES (%s, %s, %s)",
                seat_values
            )
            conn.commit()
            
            # Get the seats again
            cursor.execute("SELECT Seat_Number, Is_Booked FROM SEAT_RESERVATION WHERE Show_ID = %s ORDER BY Seat_Number", (show_id,))
            seats = cursor.fetchall()
            print(f"After auto-creation: {len(seats)} seats")
        
    except mysql.connector.Error as err:
        flash(f'Error loading show details: {err}', 'error')
        show = None
        seats = []
        print(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
    
    return render_template('book_ticket.html', show=show, seats=seats)
 
@app.route('/my_bookings')
@login_required
def my_bookings():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed!"
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Using the view we created
        cursor.execute("SELECT * FROM VIEW_BookingSummary WHERE User_Name = %s ORDER BY Show_Date DESC", 
                      (session['user_name'],))
        bookings = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error loading bookings: {err}', 'error')
        bookings = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Use dictionary=True to access Seat_Numbers easily
    
    try:
        # First, free up the seats
        cursor.execute("SELECT Show_ID, Seat_Numbers FROM BOOKING WHERE Booking_ID = %s", (booking_id,))
        booking = cursor.fetchone()
        
        if booking and booking['Seat_Numbers']:
            show_id = booking['Show_ID']
            seat_numbers = booking['Seat_Numbers'].split(',')
            
            # Use executemany for efficiency
            seat_updates = [(show_id, seat.strip()) for seat in seat_numbers]
            cursor.executemany("""
                UPDATE SEAT_RESERVATION 
                SET Is_Booked = FALSE, Booking_ID = NULL 
                WHERE Show_ID = %s AND Seat_Number = %s
            """, seat_updates)

        
        # Then cancel the booking using the procedure (handles log and payment status)
        # Note: callproc requires a simple cursor, not dictionary=True, so re-establish or ensure proper handling
        cursor.close()
        cursor = conn.cursor()
        cursor.callproc('CancelBooking', (booking_id,))
        
        conn.commit()
        flash('Booking cancelled successfully! Seats have been freed up.', 'success')
    except mysql.connector.Error as err:
        flash(f'Cancellation failed: {err}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('my_bookings'))

# Login and Register routes - UNCHANGED
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM USERS WHERE Email = %s AND Password = %s", (email, password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['User_ID']
                session['user_name'] = user['Name']
                flash('Login successful!', 'success')
                
                # Check if the user is the Admin (User_ID = 1)
                if user['User_ID'] == 1:
                    return redirect(url_for('admin_dashboard'))
                    
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials!', 'error')
        except mysql.connector.Error as err:
            flash(f'Login error: {err}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT IFNULL(MAX(User_ID), 0) + 1 FROM USERS")
            user_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO USERS (User_ID, Name, Email, Phone_No, Password) VALUES (%s, %s, %s, %s, %s)",
                (user_id, name, email, phone, password)
            )
            conn.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Queries demonstration page - UNCHANGED
@app.route('/queries')
def queries():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed!"
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Nested Query
        cursor.execute("SELECT Title, Rating FROM MOVIE WHERE Rating > (SELECT AVG(Rating) FROM MOVIE)")
        nested_query = cursor.fetchall()
        
        # Join Query
        cursor.execute("""
            SELECT m.Title, t.Name as Theatre, s.Show_Date, s.Show_Time, s.Price
            FROM SHOWS s
            JOIN MOVIE m ON s.Movie_ID = m.Movie_ID
            JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
            JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
            WHERE s.Show_Date >= CURDATE()
        """)
        join_query = cursor.fetchall()
        
        # Aggregate Query
        cursor.execute("""
            SELECT t.Name as Theatre, 
                    COUNT(b.Booking_ID) as Total_Bookings,
                    SUM(b.Total_Amount) as Total_Revenue,
                    AVG(b.Total_Amount) as Average_Booking_Value
            FROM BOOKING b
            JOIN SHOWS s ON b.Show_ID = s.Show_ID
            JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
            JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
            GROUP BY t.Theatre_ID, t.Name
        """)
        aggregate_query = cursor.fetchall()
        
        # Function demonstration - using manual calculation instead of function
        cursor.execute("SELECT AVG(Rating) as AvgRating FROM MOVIE")
        avg_rating_result = cursor.fetchone()
        avg_rating = avg_rating_result['AvgRating'] if avg_rating_result else 0
        
    except mysql.connector.Error as err:
        flash(f'Error executing queries: {err}', 'error')
        nested_query = []
        join_query = []
        aggregate_query = []
        avg_rating = 0
    finally:
        cursor.close()
        conn.close()
    
    return render_template('queries.html',
                            nested_query=nested_query,
                            join_query=join_query,
                            aggregate_query=aggregate_query,
                            avg_rating=avg_rating)

# API endpoint to check seat availability - UNCHANGED
@app.route('/api/seats/<int:show_id>')
def get_seats(show_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'})
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT Seat_Number, Is_Booked 
            FROM SEAT_RESERVATION 
            WHERE Show_ID = %s 
            ORDER BY Seat_Number
        """, (show_id,))
        seats = cursor.fetchall()
        
        return jsonify({'seats': seats})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        cursor.close()
        conn.close()

# --- NEW ADMIN ROUTES ---

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'error')
        return redirect(url_for('index'))

    cursor = conn.cursor(dictionary=True)
    all_movies = []
    current_revenue = None
    stats = {}

    try:
        # --- Handle POST request from the Revenue form ---
        if request.method == 'POST':
            movie_id = request.form.get('movie_id')
            if movie_id and movie_id.isdigit():
                # Call the Stored Function
                cursor.execute(f"SELECT CalculateMovieRevenue({movie_id}) as Revenue")
                revenue_result = cursor.fetchone()
                current_revenue = revenue_result['Revenue'] if revenue_result else 0.00
        
        # --- GET Request: Fetch all data needed for the page ---
        
        # 1. Fetch all movies for the dropdowns
        cursor.execute("SELECT Movie_ID, Title FROM MOVIE ORDER BY Title")
        all_movies = cursor.fetchall()
        
        # 2. Fetch Quick Stats
        cursor.execute("SELECT COUNT(*) as count FROM MOVIE")
        stats['total_movies'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM SHOWS")
        stats['total_shows'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM BOOKING")
        stats['total_bookings'] = cursor.fetchone()['count']
        
        # Use the revenue function for ALL movies (Movie_ID = 0 is a placeholder)
        # We need a new function for TOTAL revenue from all movies.
        # Let's use the Booking table for a simpler, accurate stat.
        cursor.execute("SELECT SUM(Total_Amount) as total FROM BOOKING WHERE Status = 'Confirmed'")
        total_rev_result = cursor.fetchone()
        stats['total_revenue'] = total_rev_result['total'] if total_rev_result['total'] else 0.00

    except mysql.connector.Error as err:
        flash(f'Database error during admin operation: {err}', 'error')
        print(f"Admin Error: {err}")
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('admin.html', 
                           stats=stats, 
                           all_movies=all_movies, 
                           current_revenue=current_revenue)

@app.route('/add_movie', methods=['POST'])
@admin_required
def add_movie():
    # Get data from the form
    title = request.form['title']
    language = request.form['language']
    genre = request.form['genre']
    duration = request.form['duration']
    rating = request.form['rating']
    image_url = request.form.get('image_url') # Get the new image_url field

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Call the new stored procedure, now passing 6 arguments
        cursor.callproc('AddNewMovie', (
            title, 
            language, 
            genre, 
            duration, 
            rating, 
            image_url  # <-- Pass the image_url here
        ))
            
        conn.commit()
        flash(f'Movie "{title}" added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding movie: {err}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/add_show', methods=['POST'])
@admin_required
def add_show():
    # Get data from the form
    movie_id = request.form['movie_id']
    screen_id = request.form['screen_id']
    show_date = request.form['show_date']
    show_time = request.form['show_time']
    price = request.form['price']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Call the stored procedure to add the show
        cursor.callproc('AddShow', (movie_id, screen_id, show_time, show_date, price))
        
        # 2. Get the new Show_ID that was just created
        cursor.execute("SELECT MAX(Show_ID) as last_id FROM SHOWS")
        new_show_id = cursor.fetchone()[0]
        
        # 3. IMPORTANT: Initialize the seats for this new show
        if new_show_id:
            cursor.callproc('InitializeSeatsForShow', (new_show_id,))
            
        conn.commit()
        flash('New show added and seats initialized!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding show: {err}', 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

# --- END NEW ADMIN ROUTES ---

if __name__ == '__main__':
    print("🎬 Starting Movie Booking System...")
    print("📍 Open http://localhost:5000 in your browser")
    # For security, turn debug=False and host='0.0.0.0' when deploying
    app.run(debug=True, host='0.0.0.0', port=5000)