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
        user["transactions"] = []
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

def send_money(sender_id, sender, receiver_id, receiver, amount, message, accepted):
    """
    Send amount from sender_id to receiver_id
    """    
    DB.send_from_sender_to_receiver(
        sender_id, sender["balance"],
        amount, receiver_id, receiver["balance"]
    )
    
    res = {"sender_id": sender_id, "receiver_id": receiver_id, "amount": amount, "message": message, "accepted": accepted}
    return success_response(res, 200)

@app.route("/api/transactions/", methods=["POST"])
def create_transaction():
    """
    Create a transaction by sending or requesting money
    """
    body = json.loads(request.data)
    sender_id = body.get("sender_id", None)
    receiver_id = body.get("receiver_id", None)
    amount = body.get("amount", None)
    message = body.get("message", None)
    accepted = body.get("accepted", None)

    if sender_id is None:
        return failure_response("bad request - please put sender id", 400)
    if receiver_id is None:
        return failure_response("bad request - please put receiver id", 400)
    if amount is None:
        return failure_response("bad request - please put amount", 400)
    if not isinstance(amount, (int, float)) or amount <= 0:
        return failure_response("bad request - amount must be a positive number", 400)
    if message is None:
        return failure_response("bad request - please put message", 400)
    
    if accepted is None:
        DB.add_request_to_transactions(sender_id, receiver_id, amount, accepted)
        res =  {"sender_id": sender_id, "receiver_id": receiver_id, "amount": amount, "message": message, "accepted": accepted}
        return res

    elif accepted == True:
        sender = DB.get_user_by_id(sender_id)
        receiver = DB.get_user_by_id(receiver_id)
    
        if sender is None or receiver is None:
            return failure_response("Sender or receiver not found", 404)
    
        if sender.get("balance") < amount:
            return failure_response("Sender has insufficient funds to perform this action", 403)
        
        send_info = send_money(sender_id, sender, receiver_id, receiver, amount, message, accepted)
        return send_info

@app.route("/api/transactions/<int:id>/", methods=[])
def accept_or_deny_request(id):
    """
    Accept or Deny a payment request
    """
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
