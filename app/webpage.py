from flask import Flask, request, render_template, jsonify, make_response
from cryptography_client import Cryptography
from bitvavo_client import bitvavo
from functools import wraps
import threading
import logger
import time
import jwt
import os


# This script hosts the webpage for controlling the bot.


# File paths
username_file = "/app/keys/username.txt"
key_file = "/app/keys/api_key.pem"
secret_file = "/app/keys/api_secret.pem"
password_file = "/app/keys/password.pem"

app = Flask(__name__)

# Get the crypto client data
crypto_client = Cryptography()
public_key_pem = crypto_client.public_key_pem

# Default route for the webpage
@app.route("/")
def index():
    return render_template("index.html")

# Check whether a password is set
with open(password_file, "r") as file:
    has_password = file.read() != ""
    
# Send API data to bitvavo if exists, else clear potentially existing data
if has_password:
    # Send bitvavo the API data
        bitvavo.initiate_api(
            crypto_client.pem_decrypt(key_file),
            crypto_client.pem_decrypt(secret_file)
        )
else:
    # Clear existing data
    with open(username_file, "w") as file:
        file.write("")
    with open(key_file, "w") as file:
        file.write("")
    with open(secret_file, "w") as file:
        file.write("")

# Get the username stored in the file, None if it doesn't exist
with open(username_file, "r") as file:
    username = file.read()
    
    
# Store sessions in-memory
sessions = {}

# Define a token key
app.config["token_key"] = os.urandom(32)

# Function to remove expired sessions
def remove_expired_sessions():
    while True:
        now = int(time.time())
        expired_ids = []
        
        # Check for all tokens whether they're expired
        for id, dump in sessions.items():
            exp_time = dump[1]
            if now > exp_time:
                expired_ids.append(id)
        
        # Delete all expired tokens
        for id in expired_ids:
            del sessions[id]
        
        time.sleep(60)

# Thread the expired session remover to run it in background
threading.Thread(target=remove_expired_sessions, daemon=True).start()

# Function to verify session tokens
def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("session_token")
        if not token:
            return jsonify({"message": "No token received"}), 401
        
        try:
            data = jwt.decode(token, app.config["token_key"], algorithms=["HS256"])
            user = sessions.get(data["session_id"])
            sent_id = request.json.get("session_id")
            if not user or data["session_id"] != sent_id or sent_id not in sessions:
                print("Invalid token")
                return jsonify({"message": "Invalid session token"}), 402
            
        except Exception:
            return jsonify({"message": "Expired token"}), 403
            
        return f(*args, **kwargs)
            
    return decorated

total_sessions = 0

# Function to generate a token for the user
def generate_token():
    # Set a new session id
    global total_sessions
    total_sessions += 1
    # Calculate the expiration time
    expiration_time = int(time.time()) + 3600 # 3600 (seconds) is 1 hour
    # Generate the token
    token = jwt.encode({
        'session_id': total_sessions,
        'exp': expiration_time
    }, app.config['token_key'], algorithm="HS256")
    
    # Create the session
    sessions[total_sessions] = [token, expiration_time]
    
    return token, total_sessions

# Route to fetch the public key
@app.route("/public-key", methods=["POST"])
def return_public_key():
    return jsonify({
        "public_key": public_key_pem.decode(),
        "username": username
    }), 200

# Route to verify the signature
@app.route("/verify-password", methods=["POST"])
def verify_password():
    encrypted_body = request.json["encrypted_data"]
    body = crypto_client.decrypt_data(encrypted_body)
    
    if crypto_client.verify_password(body.get("password")):
        # Generate a token
        token, session_id = generate_token()
        # Create a response
        response = make_response(jsonify({"session_id": session_id}))
        response.set_cookie("session_token", token, httponly=True, secure=True)
        
        return response, 200
    
    return jsonify({"message": "Incorrect password!"}), 404

# Route to store api data on first login
@app.route("/first-time-login", methods=["POST"])
def first_time_login():
    encrypted_body = request.json["encrypted_data"]
    body = crypto_client.decrypt_data(encrypted_body)
    
    # Set up the new password
    if not crypto_client.create_password(body.get("password")):
        return "Resetting account is on timeout!", 405
    
    # Use global
    global username
    
    # Get data as variables
    username = body.get("username")
    api_key = body.get("api_key")
    api_secret = body.get("api_secret")
    
    # Send bitvavo the new API data
    bitvavo.initiate_api(api_key, api_secret)
    
    # Store the username
    with open(username_file, "w") as file:
        file.write(username)
        
    # Store the API data in pem files
    crypto_client.pem_encrypt(api_key, key_file)
    crypto_client.pem_encrypt(api_secret, secret_file)
    
    # Generate a token
    token, session_id = generate_token()
    # Create a response
    response = make_response(jsonify({"session_id": session_id}))
    response.set_cookie("session_token", token, httponly=True, secure=True)
    
    logger.log("User did first time login")
    
    return response, 200

# Test function to use the token
@app.route("/use-token", methods=["POST"])
@verify_token
def use_token():
    return jsonify({"message": "Received token!"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=8000)

