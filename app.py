from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from passlib.hash import sha256_crypt
from functools import wraps
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from cachecontrol import CacheControl
from dotenv import load_dotenv
from psycopg.rows import dict_row

import re 
import os
import psycopg
import requests
import google.auth.transport.requests

import pyotp
import qrcode


load_dotenv()


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


app = Flask(__name__)
app.secret_key = get_required_env("SECRET_KEY")

# Database
DATABASE_URL = get_required_env("DATABASE_URL")
DATABASE_SSLMODE = os.getenv("DATABASE_SSLMODE")


def get_db_connection():
    connection_args = {"row_factory": dict_row}
    if DATABASE_SSLMODE:
        connection_args["sslmode"] = DATABASE_SSLMODE
    return psycopg.connect(DATABASE_URL, **connection_args)

# to allow Http traffic for local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" 

# GoogleAuth2
GOOGLE_CLIENT_ID = get_required_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_required_env("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/callback")

flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri=GOOGLE_REDIRECT_URI
)

# Regular expression pattern to enforce password requirements
password_pattern = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$')

# key for QR/Authenticator*
keyQR = pyotp.random_base32() # dynamic key randomly generated, base 32 (char a-Z, 2-7)

# Define the cipher functions here
def atbash_cipher(text):
    result = ""
    for char in text:
        if char.isalpha(): 
            if char.islower():
                result += chr(122 - ord(char) + 97)  
            else:
                result += chr(90 - ord(char) + 65)  
        else:
            result += char 
    return result

def caesar_cipher(text, key, mode):
    result = ""
    for char in text:
        if char.isalpha():
            if char.islower():
                if mode == 'e':
                    result += chr(((ord(char) - 97 - key) % 26) + 97)
                elif mode == 'd':
                    result += chr(((ord(char) - 97 + key) % 26) + 97)
            else:
                if mode == 'e':
                    result += chr(((ord(char) - 65 - key) % 26) + 65)
                elif mode == 'd':
                    result += chr(((ord(char) - 65 + key) % 26) + 65)
        else:
            result += char
    return result

def vigenere_cipher(text, keyword, decrypt=False):
    result = ""
    keyword = keyword.replace(" ", "").upper()
    key_length = len(keyword)
    key_index = 0

    for char in text:
        if char.isalpha():
            shift = ord(keyword[key_index % key_length]) - 65  # Convert the keyword character to a shift value (A=0, B=1, etc.)
            if decrypt:
                shift =- shift  # For decryption, baligtaron ang shift

            if char.islower():
                result += chr(((ord(char) - 97 + shift) % 26) + 97)
            else:
                result += chr(((ord(char) - 65 + shift) % 26) + 65)

            key_index += 1
        else:
            result += char
    return result



# home
@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect(url_for('cipher'))
    return redirect(url_for('local_login'))


# Google Login
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    expected_state = session.get("state")
    actual_state = request.args.get("state")
    if not expected_state or expected_state != actual_state:
        flash('Google login session expired. Please try again.', 'danger')
        return redirect(url_for('local_login'))

    if "code" not in request.args:
        abort(500)

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")

    # Fetch the profile picture using the Google+ API (deprecated but still working)
    profile_picture_url = f"https://www.googleapis.com/plus/v1/people/{session['google_id']}?fields=image&key={GOOGLE_CLIENT_ID}"

    # Send a GET request to fetch the profile picture
    response = requests.get(profile_picture_url)

    if response.status_code == 200:
        profile_data = response.json()
        # Extract the profile picture URL
        profile_picture_url = profile_data.get("image", {}).get("url")

        # Store the profile picture URL in the session
        session["profile_picture_url"] = profile_picture_url
    # else:
    #     flash("Failed to fetch profile picture")

    return redirect(url_for('gAuth'))


# local login
@app.route('/local_login', methods=['GET', 'POST'])
def local_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # get the user from the database by username
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    stored_hashed_password = user['password']
                    login_attempts = user['login_attempts']
                    is_blocked = user['blocked'] 

                    if is_blocked:
                        flash('Your account is blocked. Please contact support.', 'danger')
                        
                    elif sha256_crypt.verify(password, stored_hashed_password):
                        # Password is correct, allow login
                        session['logged_in'] = True
                        session['username'] = username 
                        return redirect(url_for('gAuth'))
                    else:
                        # Password is incorrect
                        login_attempts += 1

                        if login_attempts >= 3:
                            # Block the user if they exceed three wrong login attempts
                            cursor.execute("UPDATE users SET login_attempts = %s, blocked = %s WHERE username = %s", (login_attempts, True, username))
                            flash('Your account has been blocked due to multiple incorrect login attempts.', 'danger')
                        else:
                            # Update login attempts if less than three
                            cursor.execute("UPDATE users SET login_attempts = %s WHERE username = %s", (login_attempts, username))
                            flash(f'Incorrect password. You have {3 - login_attempts} attempts remaining.', 'danger')

                else:
                    flash('Username not found.', 'danger')
    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        # Check if username meets the minimum length requirement
        if len(username) < 6:
            flash('Username must be at least 6 characters long.', 'danger')
            return redirect(url_for('register'))

        # Check if password meets the minimum length requirement and pattern
        if len(password) < 8 or not password_pattern.match(password):
            flash('Password must be at least 8 characters long and contain a combination of characters, numbers, and special characters.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = sha256_crypt.hash(password)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the username is already taken
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

                if user:
                    flash('Username is already taken', 'danger')
                else:
                    # Insert the new user into the database
                    cur.execute(
                        "INSERT INTO users (username, password, login_attempts) VALUES (%s, %s, %s)",
                        (username, hashed_password, 0)
                    )

                    flash('You are now registered and can log in', 'success')
                    return redirect(url_for('local_login'))
        
    return render_template('register.html')


# Define Cipher Required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session and "google_id" not in session: # NEW
            flash('You must be logged in to access this page.', 'danger')
            return redirect(url_for('local_login'))
        return f(*args, **kwargs)
    return decorated_function

# Google Authenticator QR
@app.route('/gAuth')
def gAuth():
    if 'username' in session:
        nameFinal = session['username']
    elif 'name' in session:
        nameFinal = session['name']
    else:
        nameFinal = "Client"

    # URL Google Authenticator
    url = pyotp.totp.TOTP(keyQR).provisioning_uri(name=nameFinal, issuer_name="CipherTool")

    # Make QR Code
    img = qrcode.make(url)
    img.save("static/qrcode.png")

    return redirect(url_for('verify'))

@app.route('/makeQR', methods=['GET', 'POST'])
def makeQR():
    prefill_message = request.args.get('message', '')

    if request.method == 'POST':
        # Collect data from the form
        encrypted_message = request.form.get('encrypted_message', '').strip()
        full_name = request.form.get('fullname')
        organization = request.form.get('organization')
        address = request.form.get('Address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        notes = request.form.get('notes')

        # Combine the collected data into a single string
        qr_lines = []
        if encrypted_message:
            qr_lines.append(f"Encrypted Message: {encrypted_message}")

        optional_fields = [
            ("Full Name", full_name),
            ("Organization", organization),
            ("Address", address),
            ("Phone", phone),
            ("Email", email),
            ("Notes", notes),
        ]
        qr_lines.extend(f"{label}: {value}" for label, value in optional_fields if value)
        data_to_encode = "\n".join(qr_lines) or "CipherTool QR"

        img = qrcode.make(data_to_encode)
        img.save("static/myQR.png")

        return render_template('myQR.html', prefill_message=encrypted_message, qr_generated=True)
    return render_template('myQR.html', prefill_message=prefill_message, qr_generated=False)

# verify QR
@app.route('/googleAuth/', methods=['GET', 'POST'])
@login_required
def verify():
    error_message = None  # Initialize error_message to None
    if request.method == 'POST':
        gauth_code = request.form.get('gauth_code')
        totp = pyotp.TOTP(keyQR)
        if totp.verify(gauth_code):
            return redirect(url_for('cipher'))
        else:
            error_message = "Wrong code. Try again."

    return render_template('googleAuth.html', error_message=error_message)


# Cipher
@app.route('/cipher', methods=['GET', 'POST'])
@login_required # login_required decorator
def cipher():
    profile_picture_url = session.get("profile_picture_url")  # Get the profile picture URL from the session

    if request.method == 'POST':
        selected_cipher = request.form.get('cipher')
        message = request.form['message']
        key = request.form.get('key', '') 
        keyword = request.form.get('keyword', '')  
        encrypt_or_decrypt = request.form.get('encrypt_or_decrypt', '').strip().lower()

        if selected_cipher == 'atbash':
            encoded_message = atbash_cipher(message)

        elif selected_cipher == 'caesar':
            if key.isdigit():
                key = int(key)
                mode = encrypt_or_decrypt
                encoded_message = caesar_cipher(message, key, mode)
            else:
                flash('Invalid Caesar cipher key. Please enter an integer.', 'danger')
                return redirect(url_for('cipher'))
            
        elif selected_cipher == 'vigenere':
            if encrypt_or_decrypt in ('e', 'd'):
                if not keyword.strip():
                    flash('Invalid Vigenere cipher keyword. Please enter a keyword.', 'danger')
                    return redirect(url_for('cipher'))
                decrypt = encrypt_or_decrypt == 'd'
                encoded_message = vigenere_cipher(message, keyword, decrypt)
            else:
                flash('Invalid encryption/decryption choice. Enter "e" for encrypt or "d" for decrypt.', 'danger')
                return redirect(url_for('cipher'))
        else:
            flash('Invalid cipher selection. Please choose a valid cipher.', 'danger')
            return redirect(url_for('cipher'))
        
        return render_template(
            'cipher.html',
            result=encoded_message,
            profile_picture_url=profile_picture_url,
            selected_cipher=selected_cipher,
            message=message,
            key=key,
            keyword=keyword,
            mode=encrypt_or_decrypt
        )

    return render_template('cipher.html', profile_picture_url=profile_picture_url, selected_cipher='atbash', mode='e')

    #     return render_template('cipher.html', result=encoded_message)
    # return render_template('cipher.html')

# @app.route('/myQR.html', methods=['GET', 'POST'])
# def myQR():
#     if request.method == 'POST':
#         fullname = request.form['fullname']


#     return render_template('myQR.html')

# @app.route('/myQr', methods=['GET', 'POST'])
# def generateQR():
#     return 0

@app.route('/myQR')
def myQR():
    return render_template('myQR.html', prefill_message=request.args.get('message', ''), qr_generated=False)


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('local_login'))

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=5000, debug=True)
