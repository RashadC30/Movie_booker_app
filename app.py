import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = "Movie_Booker.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with simple movies and showtimes."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS showtimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                ticket_price REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                showtime_id INTEGER NOT NULL,
                seat_code TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                FOREIGN KEY (showtime_id) REFERENCES showtimes (id),
                UNIQUE (showtime_id, seat_code)
            );        
        """)
        cursor = conn.execute("SELECT COUNT(*) FROM showtimes")
        if cursor.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO showtimes (movie_title, start_time, ticket_price) VALUES (?, ?, ?)",
                [
                    ("Project Hail Mary", "4:30 PM", 15.50),
                    ("The Super Mario Galaxy Movie", "6:00 PM", 12.75),
                    ("Resident Evil", "7:30 PM", 15.50),
                    ("GOAT", "6:50 PM", 12.75),
                    
                ]
            )
@app.route("/")
def index():
    with get_db() as conn:
        showtimes = conn.execute("SELECT * FROM showtimes").fetchall()
    return render_template("index.html", showtimes=showtimes)

@app.route("/api/seats/<int:showtime_id>", methods=["GET"])
def get_booked_seats(showtime_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT seat_code FROM bookings WHERE showtime_id = ?", (showtime_id,)
        ).fetchall()
    return jsonify({"booked_seats": [row["seat_code"] for row in rows]})

@app.route("/api/book", methods=["POST"])
def book_seats():
    data = request.get_json()
    showtime_id = data.get("showtime_id")
    seats = data.get("seats", [])
    customer_name = data.get("customer_name", "").strip()
    
    if not showtime_id or not seats or not customer_name:
        return jsonify({"error": "Missing reqired booking details."}), 400
    
    try:
        with get_db() as conn:
            for seat in seats:
                conn.execute(
                    "INSERT INTO bookings (showtime_id, seat_code, customer_name) VALUES (?, ?, ?)",
                    (showtime_id, seat, customer_name)
                )
        return jsonify({"message": f"Successfully booked {', '.join(seats)} for {customer_name}!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "One or more selected seats were just booked by someone else. Please try again."}), 409
    
if __name__=="__main__":
    init_db()
    app.run(debug=True)