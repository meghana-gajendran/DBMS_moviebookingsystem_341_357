-- Step 1: Create the database
CREATE DATABASE MovieBookingSystem;

-- Step 2: Use the database
USE MovieBookingSystem;

-- Step 3: Create the tables (your DDL)
-- THEATRE Table
CREATE TABLE THEATRE (
    Theatre_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Location VARCHAR(150),
    City VARCHAR(100)
);

-- SCREEN Table
CREATE TABLE SCREEN (
    Screen_ID INT PRIMARY KEY,
    Theatre_ID INT NOT NULL,
    Screen_Number INT NOT NULL,
    Total_Seats INT NOT NULL,
    FOREIGN KEY (Theatre_ID) REFERENCES THEATRE(Theatre_ID)
);

-- MOVIE Table
CREATE TABLE MOVIE (
    Movie_ID INT PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    Language VARCHAR(50),
    Genre VARCHAR(50),
    Duration INT,
    Rating DECIMAL(2,1)
);

-- SHOW Table
CREATE TABLE SHOWS (
    Show_ID INT PRIMARY KEY,
    Movie_ID INT NOT NULL,
    Screen_ID INT NOT NULL,
    Show_Time TIME NOT NULL,
    Show_Date DATE NOT NULL,
    Price DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (Movie_ID) REFERENCES MOVIE(Movie_ID),
    FOREIGN KEY (Screen_ID) REFERENCES SCREEN(Screen_ID)
);

-- USERS Table
CREATE TABLE USERS (
    User_ID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Phone_No VARCHAR(15) UNIQUE,
    Password VARCHAR(100) NOT NULL
);

-- BOOKING Table
CREATE TABLE BOOKING (
    Booking_ID INT PRIMARY KEY,
    Show_ID INT NOT NULL,
    User_ID INT NOT NULL,
    Seats_Booked INT NOT NULL,
    Booking_Date DATE NOT NULL,
    Total_Amount DECIMAL(10,2) NOT NULL,
    Status VARCHAR(50) DEFAULT 'Pending',
    Seat_Numbers VARCHAR(255) NULL,
    FOREIGN KEY (Show_ID) REFERENCES SHOWS(Show_ID),
    FOREIGN KEY (User_ID) REFERENCES USERS(User_ID)
);

-- PAYMENT Table
CREATE TABLE PAYMENT (
    Payment_ID INT PRIMARY KEY,
    Booking_ID INT NOT NULL UNIQUE,
    Amount DECIMAL(10,2) NOT NULL,
    Payment_Mode VARCHAR(50),
    Payment_State VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (Booking_ID) REFERENCES BOOKING(Booking_ID)
);

-- SEAT RESERVATION Table (NEW - for seat selection)
CREATE TABLE SEAT_RESERVATION (
    Reservation_ID INT AUTO_INCREMENT PRIMARY KEY,
    Show_ID INT NOT NULL,
    Seat_Number VARCHAR(10) NOT NULL,
    Is_Booked BOOLEAN DEFAULT FALSE,
    Booking_ID INT NULL,
    FOREIGN KEY (Show_ID) REFERENCES SHOWS(Show_ID),
    FOREIGN KEY (Booking_ID) REFERENCES BOOKING(Booking_ID),
    UNIQUE KEY unique_seat_show (Show_ID, Seat_Number)
);

-- AUDIT TABLES
CREATE TABLE MOVIE_LOG (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    Movie_ID INT,
    Title VARCHAR(200),
    Added_On TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE CANCEL_LOG (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    Booking_ID INT,
    Cancelled_On TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO THEATRE VALUES
(1, 'PVR Cinemas', 'Orion Mall', 'Bangalore'),
(2, 'INOX', 'Mantri Square', 'Bangalore'),
(3, 'Cinepolis', 'Phoenix Marketcity', 'Chennai'),
(4, 'IMAX', 'Forum Mall', 'Bangalore'),
(5, 'Carnival Cinemas', 'Grand Mall', 'Chennai');

INSERT INTO SCREEN VALUES
(1, 1, 1, 120),
(2, 1, 2, 100),
(3, 2, 1, 150),
(4, 3, 1, 130),
(5, 4, 1, 200),
(6, 4, 2, 180),
(7, 5, 1, 160);

INSERT INTO MOVIE VALUES
(101, 'Inception', 'English', 'Sci-Fi', 148, 8.8),
(102, 'KGF Chapter 2', 'Kannada', 'Action', 170, 8.5),
(103, 'Jawan', 'Hindi', 'Action', 165, 7.9),
(104, 'Avatar: The Way of Water', 'English', 'Sci-Fi', 192, 7.6),
(105, 'RRR', 'Telugu', 'Action', 187, 8.0),
(106, 'The Dark Knight', 'English', 'Action', 152, 9.0),
(107, 'Interstellar', 'English', 'Sci-Fi', 169, 8.6);



INSERT INTO USERS VALUES
(1, 'Nohara', 'nohara@example.com', '9876543210', 'mahima123'),
(2, 'Ravi Kumar', 'ravi@example.com', '9123456780', 'ravi@123'),
(3, 'Sneha Rao', 'sneha@example.com', '9988776655', 'sneha@pass'),
(4, 'Priya Sharma', 'priya@example.com', '9112233445', 'priya123'),
(5, 'Amit Patel', 'amit@example.com', '9223344556', 'amit@123');

INSERT INTO BOOKING VALUES
(301, 201, 1, 2, CURDATE(), 500.00, 'Confirmed', 'A1,A2'),
(302, 202, 2, 3, CURDATE(), 900.00, 'Pending', 'B1,B2,B3'),
(303, 203, 3, 1, CURDATE(), 200.00, 'Confirmed', 'C5'),
(304, 204, 4, 2, CURDATE(), 700.00, 'Confirmed', 'D3,D4'),
(305, 205, 5, 4, CURDATE(), 1400.00, 'Pending', 'E1,E2,E3,E4'),
(306, 206, 1, 1, CURDATE(), 280.00, 'Confirmed', 'F7');

INSERT INTO PAYMENT VALUES
(401, 301, 500.00, 'Credit Card', 'Completed'),
(402, 302, 900.00, 'UPI', 'Pending'),
(403, 303, 200.00, 'Cash', 'Completed'),
(404, 304, 700.00, 'Credit Card', 'Completed'),
(405, 305, 1400.00, 'UPI', 'Pending'),
(406, 306, 280.00, 'Debit Card', 'Completed');

-- Functions
DELIMITER //
CREATE FUNCTION CalculateTotalAmount(
    p_ShowID INT,
    p_Seats INT
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE showPrice DECIMAL(10,2);
    DECLARE total DECIMAL(10,2);

    SELECT Price INTO showPrice FROM SHOWS WHERE Show_ID = p_ShowID;
    SET total = showPrice * p_Seats;
    RETURN total;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetMovieDuration(p_MovieID INT)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE dur INT;
    DECLARE result VARCHAR(20);
    SELECT Duration INTO dur FROM MOVIE WHERE Movie_ID = p_MovieID;
    SET result = CONCAT(FLOOR(dur/60), 'h ', MOD(dur,60), 'm');
    RETURN result;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetAverageRating()
RETURNS DECIMAL(3,2)
DETERMINISTIC
BEGIN
    DECLARE avgRating DECIMAL(3,2);
    SELECT AVG(Rating) INTO avgRating FROM MOVIE;
    RETURN avgRating;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetAvailableSeats(p_ShowID INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT;
    DECLARE booked INT;
    DECLARE available INT;
    SELECT s.Total_Seats INTO total
    FROM SCREEN s JOIN SHOWS sh ON s.Screen_ID = sh.Screen_ID
    WHERE sh.Show_ID = p_ShowID;
    SELECT IFNULL(SUM(b.Seats_Booked),0) INTO booked FROM BOOKING b WHERE b.Show_ID = p_ShowID;
    SET available = total - booked;
    RETURN available;
END //
DELIMITER ;

-- NEW FUNCTION: Initialize seats for a show
DELIMITER //
CREATE PROCEDURE InitializeSeatsForShow(IN p_ShowID INT)
BEGIN
    DECLARE total_seats INT;
    DECLARE i INT DEFAULT 1;
    DECLARE rows1 INT DEFAULT 1;
    DECLARE seats_per_row INT DEFAULT 10;
    DECLARE seat_number VARCHAR(10);
    
    -- Get total seats for the screen
    SELECT Total_Seats INTO total_seats 
    FROM SCREEN sc 
    JOIN SHOWS sh ON sc.Screen_ID = sh.Screen_ID 
    WHERE sh.Show_ID = p_ShowID;
    
    -- Calculate rows and seats per row
    SET seats_per_row = 10;
    SET rows1 = CEIL(total_seats / seats_per_row);
    
    -- Delete existing seats for this show
    DELETE FROM SEAT_RESERVATION WHERE Show_ID = p_ShowID;
    
    -- Insert new seats
    WHILE i <= total_seats DO
        SET seat_number = CONCAT(CHAR(64 + CEIL(i / seats_per_row)), MOD(i-1, seats_per_row) + 1);
        INSERT INTO SEAT_RESERVATION (Show_ID, Seat_Number, Is_Booked) 
        VALUES (p_ShowID, seat_number, FALSE);
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

-- Procedures
DELIMITER //
CREATE PROCEDURE BookTicket(
    IN p_ShowID INT,
    IN p_UserID INT,
    IN p_Seats INT,
    IN p_PaymentMode VARCHAR(50)
)
BEGIN
    DECLARE v_Total DECIMAL(10,2);
    DECLARE v_BookingID INT;
    DECLARE v_PaymentID INT;

    -- Check seat availability
    IF GetAvailableSeats(p_ShowID) < p_Seats THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough seats available!';
    END IF;

    -- Calculate total amount
    SET v_Total = CalculateTotalAmount(p_ShowID, p_Seats);

    -- Generate next booking id
    SELECT IFNULL(MAX(Booking_ID), 300) + 1 INTO v_BookingID FROM BOOKING;

    INSERT INTO BOOKING (Booking_ID, Show_ID, User_ID, Seats_Booked, Booking_Date, Total_Amount, Status)
    VALUES (v_BookingID, p_ShowID, p_UserID, p_Seats, CURDATE(), v_Total, 'Pending');

    -- Payment
    SELECT IFNULL(MAX(Payment_ID), 400) + 1 INTO v_PaymentID FROM PAYMENT;
    INSERT INTO PAYMENT (Payment_ID, Booking_ID, Amount, Payment_Mode, Payment_State)
    VALUES (v_PaymentID, v_BookingID, v_Total, p_PaymentMode, 'Pending');
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE UpdatePaymentStatus(IN p_BookingID INT, IN p_State VARCHAR(50))
BEGIN
    UPDATE PAYMENT SET Payment_State = p_State WHERE Booking_ID = p_BookingID;
    IF p_State = 'Completed' THEN
        UPDATE BOOKING SET Status = 'Confirmed' WHERE Booking_ID = p_BookingID;
    ELSE
        UPDATE BOOKING SET Status = 'Pending' WHERE Booking_ID = p_BookingID;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE CancelBooking(IN p_BookingID INT)
BEGIN
    UPDATE BOOKING SET Status = 'Cancelled' WHERE Booking_ID = p_BookingID;
    UPDATE PAYMENT SET Payment_State = 'Refunded' WHERE Booking_ID = p_BookingID;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE AddNewMovie(
    IN p_Title VARCHAR(200),
    IN p_Language VARCHAR(50),
    IN p_Genre VARCHAR(50),
    IN p_Duration INT,
    IN p_Rating DECIMAL(2,1)
)
BEGIN
    DECLARE newID INT;
    SELECT IFNULL(MAX(Movie_ID),100) + 1 INTO newID FROM MOVIE;
    INSERT INTO MOVIE VALUES (newID, p_Title, p_Language, p_Genre, p_Duration, p_Rating);
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE AddShow(
    IN p_MovieID INT,
    IN p_ScreenID INT,
    IN p_Time TIME,
    IN p_Date DATE,
    IN p_Price DECIMAL(8,2)
)
BEGIN
    DECLARE newShowID INT;
    SELECT IFNULL(MAX(Show_ID),200) + 1 INTO newShowID FROM SHOWS;
    INSERT INTO SHOWS VALUES (newShowID, p_MovieID, p_ScreenID, p_Time, p_Date, p_Price);
END //
DELIMITER ;

-- Triggers
DELIMITER //
CREATE TRIGGER trg_AfterPaymentUpdate
AFTER UPDATE ON PAYMENT
FOR EACH ROW
BEGIN
    IF NEW.Payment_State = 'Completed' THEN
        UPDATE BOOKING SET Status = 'Confirmed'
        WHERE Booking_ID = NEW.Booking_ID;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_BeforeBookingInsert
BEFORE INSERT ON BOOKING
FOR EACH ROW
BEGIN
    DECLARE available INT;
    SET available = GetAvailableSeats(NEW.Show_ID);
    IF available < NEW.Seats_Booked THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Not enough seats available!';
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_BeforeBookingDate
BEFORE INSERT ON BOOKING
FOR EACH ROW
BEGIN
    IF NEW.Booking_Date IS NULL THEN
        SET NEW.Booking_Date = CURDATE();
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_AfterMovieInsert
AFTER INSERT ON MOVIE
FOR EACH ROW
BEGIN
    INSERT INTO MOVIE_LOG (Movie_ID, Title)
    VALUES (NEW.Movie_ID, NEW.Title);
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_AfterBookingCancel
AFTER UPDATE ON BOOKING
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Cancelled' AND OLD.Status != 'Cancelled' THEN
        INSERT INTO CANCEL_LOG (Booking_ID) VALUES (NEW.Booking_ID);
    END IF;
END //
DELIMITER ;

-- View
CREATE OR REPLACE VIEW VIEW_BookingSummary AS
SELECT 
    b.Booking_ID,
    u.Name AS User_Name,
    m.Title AS Movie_Title,
    sh.Show_Date,
    sh.Show_Time,
    t.Name AS Theatre_Name,
    b.Seats_Booked,
    b.Seat_Numbers,
    b.Total_Amount,
    p.Payment_Mode,
    p.Payment_State,
    b.Status AS Booking_Status
FROM BOOKING b
JOIN USERS u ON b.User_ID = u.User_ID
JOIN SHOWS sh ON b.Show_ID = sh.Show_ID
JOIN MOVIE m ON sh.Movie_ID = m.Movie_ID
JOIN SCREEN sc ON sh.Screen_ID = sc.Screen_ID
JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
JOIN PAYMENT p ON b.Booking_ID = p.Booking_ID;

-- Initialize seats for all shows
CALL InitializeSeatsForShow(201);
CALL InitializeSeatsForShow(202);
CALL InitializeSeatsForShow(203);
CALL InitializeSeatsForShow(204);
CALL InitializeSeatsForShow(205);
CALL InitializeSeatsForShow(206);
CALL InitializeSeatsForShow(207);
CALL InitializeSeatsForShow(208);
CALL InitializeSeatsForShow(209);
CALL InitializeSeatsForShow(210);
CALL InitializeSeatsForShow(211);
CALL InitializeSeatsForShow(212);
CALL InitializeSeatsForShow(213);
CALL InitializeSeatsForShow(214);
CALL InitializeSeatsForShow(215);
CALL InitializeSeatsForShow(216);
CALL InitializeSeatsForShow(217);

-- Mark some seats as booked to demonstrate the system
UPDATE SEAT_RESERVATION SET Is_Booked = TRUE, Booking_ID = 301 WHERE Show_ID = 209 AND Seat_Number IN ('A1', 'A2', 'A3', 'B5', 'B6');
UPDATE SEAT_RESERVATION SET Is_Booked = TRUE, Booking_ID = 302 WHERE Show_ID = 209 AND Seat_Number IN ('C1', 'C2', 'C3');
UPDATE SEAT_RESERVATION SET Is_Booked = TRUE, Booking_ID = 303 WHERE Show_ID = 210 AND Seat_Number IN ('D1', 'D2', 'E5', 'E6');

-- Test queries
SELECT 'Database Setup Complete' as Status;

-- Show available shows for The Dark Knight
SELECT 
    s.Show_ID,
    m.Title,
    t.Name as Theatre_Name,
    s.Show_Date,
    s.Show_Time,
    s.Price,
    GetAvailableSeats(s.Show_ID) as Available_Seats
FROM SHOWS s
JOIN MOVIE m ON s.Movie_ID = m.Movie_ID
JOIN SCREEN sc ON s.Screen_ID = sc.Screen_ID
JOIN THEATRE t ON sc.Theatre_ID = t.Theatre_ID
WHERE m.Title = 'The Dark Knight' AND s.Show_Date >= CURDATE()
ORDER BY s.Show_Date, s.Show_Time;

-- Show seat layout for a specific show
SELECT 
    Show_ID,
    Seat_Number,
    Is_Booked
FROM SEAT_RESERVATION 
WHERE Show_ID = 209 
ORDER BY 
    SUBSTRING(Seat_Number, 1, 1),
    CAST(SUBSTRING(Seat_Number, 2) AS UNSIGNED);

-- Test functions
SELECT 
    Show_ID, 
    GetAvailableSeats(Show_ID) as Available_Seats 
FROM SHOWS 
WHERE Show_ID = 209;









SELECT 
    s.Show_ID,
    m.Title,
    COUNT(sr.Seat_Number) as total_seats,
    sr.Show_ID as seat_show_id
FROM SHOWS s
JOIN MOVIE m ON s.Movie_ID = m.Movie_ID
LEFT JOIN SEAT_RESERVATION sr ON s.Show_ID = sr.Show_ID
WHERE s.Show_ID = 201
GROUP BY s.Show_ID, m.Title;


SELECT * FROM SEAT_RESERVATION WHERE Show_ID = 201 LIMIT 10;


-- p oijhgfds

ALTER TABLE BOOKING ADD COLUMN Seat_Numbers VARCHAR(255) NULL AFTER Status;
INSERT INTO SEAT_RESERVATION (Show_ID, Seat_Number, Is_Booked)
SELECT 
    203 as Show_ID,
    CONCAT(CHAR(64 + FLOOR((n-1)/10) + 1), MOD(n-1, 10) + 1) as Seat_Number,
    FALSE as Is_Booked
FROM (
    SELECT a.N + b.N * 10 + 1 as n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11) b
) numbers
WHERE n <= 120;


DELIMITER //
CREATE FUNCTION CalculateMovieRevenue(p_MovieID INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE totalRevenue DECIMAL(10,2);

    -- Only counts revenue from confirmed (paid) bookings
    SELECT IFNULL(SUM(b.Total_Amount), 0.00) INTO totalRevenue
    FROM BOOKING b
    JOIN SHOWS s ON b.Show_ID = s.Show_ID
    WHERE s.Movie_ID = p_MovieID 
      AND b.Status = 'Confirmed'; 

    RETURN totalRevenue;
END //
DELIMITER ;


-- SELECT User_ID, Name, Email, Password 
-- FROM USERS 
-- WHERE User_ID = 1;   #############ADMIN CREDENTIALS