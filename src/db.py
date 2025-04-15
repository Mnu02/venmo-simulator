import os
import sqlite3

# From: https://goo.gl/YzypOI
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Task app.
    Handles with reading and writing data with the database.
    """

    def __init__(self):
        self.conn = sqlite3.connect("venmo.db", check_same_thread=False)
        self.create_venmo_table()

    def create_venmo_table(self):
        """
        Create a table with user id, name, username and balance
        """
        try:
            self.conn.execute("""
                CREATE TABLE venmo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT,
                balance REAL DEFAULT 0
                );
        """)
        except Exception as e:
            print(e)

    def get_all_users(self):
        """
        Get all users from database. Exclude the user balance
        """
        cursor = self.conn.execute("SELECT * FROM venmo;")
        users = []
        for row in cursor:
            users.append({"id": row[0], "name": row[1], "username": row[2]})
        return users
    
    def create_a_user(self, name, username, balance):
        """
        Create a user
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO venmo (name, username, balance) values (?, ?, ?);", (name, username, balance))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_by_id(self, user_id):
        """
        Get a user with a specific user_id
        """
        cursor = self.conn.execute("SELECT * FROM venmo WHERE id = ?;", (user_id,))
        for row in cursor:
            return {"id": row[0], "name": row[1], "username": row[2], "balance": row[3]}
        return None


    def delete_specific_user(self, user_id):
        """
        Delete a specific user from the database
        """
        self.conn.execute("DELETE FROM venmo WHERE id = ?;", (user_id,))
        self.conn.commit()


    def send_from_sender_to_receiver(self, sender_id, sender_amt, amount, receiver_id, receiver_amt):
        """
        Send money from sender_id to receiver_id
        """
        self.conn.execute("UPDATE venmo SET balance = ? WHERE id = ?;", (sender_amt-amount, sender_id))
        self.conn.execute("UPDATE venmo SET balance = ? WHERE id = ?;", (receiver_amt+amount, receiver_id))
        self.conn.commit()
        

# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
