import json
from flask import Flask, request
import db

DB = db.DatabaseDriver()

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello world!"

def success_response(body, code=200):
    return json.dumps(body), code

def failure_response(message, code=404):
    return json.dumps({'error': message}), code
def success_response(body, code=200):
    return json.dumps(body), code

def failure_response(message, code=404):
    return json.dumps({'error': message}), code

# your routes here
@app.route("/api/users/", methods=["GET"])
def get_all_users():
    return success_response({"users": DB.get_all_users()})

@app.route("/api/users/", methods=["POST"])
def create_a_user():
    """
    Create a user
    """
    body = json.loads(request.data)

    if "name" not in body:
        return failure_response("'name' is required!", 400)
    if "username" not in body:
        return failure_response("'username' is required!", 400)
    
    name = body["name"]
    username = body["username"]
    balance = body["balance"] if "balance" in body else 0

    try:
        user_id = DB.create_a_user(name, username, balance)
        user = DB.get_user_by_id(user_id)
        if user is None:
            return failure_response("User not found!", 404)
        return success_response(user, 201)
    except Exception as e:
        print("❌ Error creating user:", e)
        return failure_response(str(e), 500)


@app.route("/api/user/<int:user_id>/", methods=["GET"])
def get_user_by_id(user_id):
    """
    Get a user with a specific user_id
    """
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found", 404)
    return success_response(user)


@app.route("/api/user/<int:user_id>/", methods=["DELETE"])
def delete_specific_user(user_id):
    """
    Delete specific user
    """
    user = DB.get_user_by_id(user_id)
    if user is None:
        return failure_response("User not found", 404)
    DB.delete_specific_user(user_id)
    return success_response(user)


@app.route("/api/send/", methods=["POST"])
def send_money():
    """
    Send money from one user id to another
    """
    body = json.loads(request.data)
    
    sender_id = body.get("sender_id", None)
    receiver_id = body.get("receiver_id", None)
    amount = body.get("amount", None)

    if sender_id is None:
        return failure_response("Include valid sender id", 400)
    if receiver_id is None:
        return failure_response("Include valid receiver id", 400)
    if amount is None:
        return failure_response("Include valid amount", 400)
    
    sender = DB.get_user_by_id(sender_id)
    receiver = DB.get_user_by_id(receiver_id)

    if sender is None or receiver is None:
        return failure_response("Sender or receiver not found", 404)
    
    if sender.get("balance") < amount:
        return failure_response("Sender has insufficient funds to perform this action", 400)
    
    DB.send_from_sender_to_receiver(
        sender_id, sender["balance"],
        amount, receiver_id, receiver["balance"]
    )
    
    res = {"sender_id": sender_id, "receiver_id": receiver_id, "amount": amount}
    return success_response(res, 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
