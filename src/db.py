import os
import sqlite3
from datetime import datetime

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
        self.create_transactions_table()

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
            print(e, flush=True)

    def create_transactions_table(self):
        """
        Create a table with transaction id, timestamp, sender_id, receiver_id, and 
        accepted fields
        """
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'now')),
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    amount REAL,
                    message TEXT,
                    accepted BOOLEAN DEFAULT NULL,
                    FOREIGN KEY (sender_id) REFERENCES venmo(id),
                    FOREIGN KEY (receiver_id) REFERENCES venmo(id)
                );
            """)
        except Exception as e:
            print(e, flush=True)

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
        row = cursor.fetchone()

        if row is None:
            return None # maybe see if you are handling None values
            
        user = {"id": row[0], "name": row[1], "username": row[2], "balance": row[3]}

        cursor = self.conn.execute("""
            SELECT * FROM transactions 
            WHERE sender_id = ? OR receiver_id = ?
            ORDER BY timestamp DESC;
        """, (user_id, user_id,))

        transactions = []
        for transaction in cursor.fetchall():
            transactions.append({
                "id": transaction[0],
                "timestamp": transaction[1],
                "sender_id": transaction[2],
                "receiver_id": transaction[3],
                "amount": transaction[4],
                "message": transaction[5],  
                "accepted": transaction[6]
            })

        user["transactions"] = transactions
        return user


    def delete_specific_user(self, user_id):
        """
        Delete a specific user from the database
        """
        self.conn.execute("DELETE FROM venmo WHERE id = ?;", (user_id,))
        self.conn.commit()

    def current_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def send_from_sender_to_receiver(self, sender_id, sender_amt, amount, receiver_id, receiver_amt, message):
        """
        Send money from sender_id to receiver_id
        """
        self.conn.execute("UPDATE venmo SET balance = ? WHERE id = ?;", (sender_amt-amount, sender_id))
        self.conn.execute("UPDATE venmo SET balance = ? WHERE id = ?;", (receiver_amt+amount, receiver_id))
        self.conn.execute("INSERT INTO transactions (timestamp, sender_id, receiver_id, amount, message, accepted) VALUES (?, ?, ?, ?, ?, ?)", 
                          (
                              self.current_timestamp(),
                              sender_id, 
                              receiver_id, 
                              amount,
                              message,
                              True,
                          ))
        self.conn.commit()

    def add_request_to_transactions(self, sender_id, receiver_id, amount, accepted, message):
        """
        Add a request into the transactions table
        """
        self.conn.execute("INSERT INTO transactions (timestamp, sender_id, receiver_id, amount, message, accepted) VALUES (?, ?, ?, ?, ?, ?)",
                          (
                              self.current_timestamp(),
                              sender_id, 
                              receiver_id,
                              amount,
                              message,
                              accepted,
                          ))
        self.conn.commit()

    def update_accepted_status(self,id, status):
        """
        Update the status of transaction with ID id
        """
        self.conn.execute("UPDATE transactions SET accepted = ?, timestamp = ? WHERE id = ?;", (status, self.current_timestamp(), id,))
        self.conn.commit()

    def get_transaction_by_id(self, id):
        """
        Get transaction by id
        """
        cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?;", (id,))
        row = cursor.fetchone()
        if row is None:
            return None

        # assuming your transactions table schema is:
        # id, timestamp, sender_id, receiver_id, amount, accepted
        return {
            "id": row[0],
            "timestamp": row[1],
            "sender_id": row[2],
            "receiver_id": row[3],
            "amount": row[4],
            "message": row[5],
            "accepted": row[6]
        }
    
    def get_last_transaction_id(self):
        cursor = self.conn.execute("SELECT last_insert_rowid();")
        return cursor.fetchone()[0]
    
    def accept_transaction_request(self, transaction_id, sender, receiver, amount):
        """
        Accepts a pending transaction: updates balances and marks as accepted.
        """
        # Update sender and receiver balances
        self.conn.execute(
            "UPDATE venmo SET balance = ? WHERE id = ?;",
            (sender["balance"] - amount, sender["id"])
        )
        self.conn.execute(
            "UPDATE venmo SET balance = ? WHERE id = ?;",
            (receiver["balance"] + amount, receiver["id"])
        )
        
        # Update the transaction's accepted status
        self.conn.execute(
            "UPDATE transactions SET accepted = ?, timestamp = ? WHERE id = ?;",
            (True, self.current_timestamp(), transaction_id)
        )
        self.conn.commit()


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
