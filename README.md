# DBMS Mini-Project: Movie Booking System
**Course:** DATABASE MANAGEMENT SYSTEM (UE23CS351A) 

This is a complete web application for a movie booking system, built as a mini-project for PES University. The application provides a seamless interface for users to browse movies and book tickets, and a powerful admin panel for site management. It is built using Python (Flask) and a relational MySQL database.

---

## 🚀 Features

This project fulfills all the primary requirements of a database application, including full CRUD functionality  and advanced logic.

### User Features
* **Browse Movies:** View all available movies with details like posters, genre, and ratings.
* **View Shows:** See upcoming shows for a specific movie, including theatre, time, and price.
* **Book Tickets:** A complete booking process, including a visual seat-selection map.
* **User Accounts:** Users can register, log in, and log out.
* **View Bookings:** Users can see a history of their own bookings and cancel them.

### Admin Features (With GUI)
* **Admin Dashboard:** A private admin panel (for User ID 1) to manage the entire site.
* **Add Movies:** Admin can add new movies (including title, poster URL, rating, etc.).
* **Add Shows:** Admin can schedule new shows for any movie at any screen.
* **View Revenue:** Admin can check the total confirmed revenue for any movie.
* **View Stats:** The dashboard shows quick stats for total movies, shows, bookings, and revenue.

---

## 🛠️ Tech Stack

This project uses a relational database and a web-based front-end.

* **Backend:** Python (Flask)
* **Database:** MySQL
* **Frontend:** HTML, CSS (Bootstrap)
* **Tools:** MySQL Workbench, Git

---

## 📦 Database Design

The core of this project is its relational database, which demonstrates advanced DBMS concepts.

* **ER Diagram & Relational Schema:** The database is designed with 10 tables, including `MOVIE`, `THEATRE`, `SCREEN`, `SHOWS`, `USERS`, `BOOKING`, `PAYMENT`, and `SEAT_RESERVATION`. This well-structured design (exceeding the 4-5 entity requirement ) ensures data integrity.
* **Normalization:** The schema is in **3NF** to reduce redundancy and improve data consistency. For example, show details are in `SHOWS`, and bookings simply reference a `Show_ID`.
* **Stored Procedures:** All major business logic is handled by the database, not the app.
    * `AddNewMovie()`: Safely adds a new movie.
    * `AddShow()`: Adds a new show.
    * `InitializeSeatsForShow()`: Automatically creates the seat map for a new show.
    * `BookTicket()`: A safe, all-in-one procedure that checks seat availability, creates a booking, and creates a payment record.
* **Stored Functions:** Used as "calculators" for the application.
    * `CalculateMovieRevenue()`: Calculates total revenue for a movie (used by admin).
    * `GetAvailableSeats()`: Calculates available seats for a show (used by booking page).
* **Triggers:** Used for automated auditing and logging.
    * `trg_AfterMovieInsert`: Automatically logs a new movie in the `MOVIE_LOG` table.
    * `trg_AfterBookingCancel`: Automatically logs a cancellation in the `CANCEL_LOG` table.
* **Complex Queries:** The application demonstrates `JOIN`, `Nested`, and `Aggregate` queries with a GUI, as seen on the `/queries` page.

---

## ⚙️ How to Run

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/meghana-gajendran/DBMS_moviebookingsystem_341_357.git
    cd DBMS_moviebookingsystem_341_357
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up the Database:**
    * Open `MovieBookingSystem.sql` in MySQL Workbench and run the entire script. This will create the database, all tables, triggers, and procedures, and insert all the sample data.
    * In `app.py`, update the `db_config` dictionary with your local MySQL password.
5.  **Run the app:**
    ```bash
    python app.py
    ```
6.  **Open the application:**
    * Go to `http://localhost:5000` in your browser.
    * **Admin Login:** `nohara@example.com` / `mahima123`
