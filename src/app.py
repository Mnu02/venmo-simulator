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

# your routes here
@app.route("/api/users/", method=["GET"])
def get_all_users():
    return success_response(DB.get_all_users())

@app.route("/api/users", method=["POST"])
def create_a_user():
    body = json.loads(request.data)

    if "name" not in body:
        return failure_response("'name' is required!", 400)
    if "username" not in body:
        return failure_response("'username' is required!", 400)
    
    name = body["name"]
    username = body["username"]
    balance = body["balance"] if "balance" in body else 0

    user_id = DB.create_a_user(name, username, balance)
    user = DB.get_user_by_id(user_id)
    
    if user is None:
        return failure_response("User not found!", 404)
    return success_response(user, 201)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
