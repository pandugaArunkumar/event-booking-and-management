import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="event_user",
        password="event123",
        database="event_booking"
    )
