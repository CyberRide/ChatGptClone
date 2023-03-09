# Importing necessary modules
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import mysql.connector
from bcrypt import checkpw, gensalt, hashpw
import openai
# Importing additional modules
import base64
import json
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import uuid
import requests
import src.services as services
import string
from urllib.parse import unquote_plus
from oauthlib.oauth2 import WebApplicationClient
import requests
from dotenv import load_dotenv
import os



app = Flask(__name__)
app.secret_key = 'chatgptclone123'
key = b'abc123abc123abc123abc123abc123abc123abc123'

processed_first_input = False

load_dotenv()
# Access environment variables using os.environ.get('KEY')
openai.api_key = os.environ.get('OPENAI_API_KEY')
mysql_user = os.environ.get('MYSQL_USER')
mysql_password = os.environ.get('MYSQL_PASSWORD')
mysql_host = os.environ.get('MYSQL_HOST')
mysql_database = os.environ.get('MYSQL_DATABASE')
GOOGLE_CLIENT_ID= os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
# Connect to MySQL database
cnx = mysql.connector.connect(user=mysql_user,
                              password=mysql_password,
                              host=mysql_host,
                              database=mysql_database)
cursor = cnx.cursor()

# Use Google configuration
client = WebApplicationClient(GOOGLE_CLIENT_ID)
google_discovery_url = GOOGLE_DISCOVERY_URL


def generate_password(length=10):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password


# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Index


@app.route("/")
def index():
    if 'username' not in session:
        return render_template('home.html')
    else:
        now = datetime.now()
        month = now.strftime("%B")  # full month name, e.g. January
        day = now.strftime("%d")  # day of the month, e.g. 01
        version = "1.0"  # your app version
        username = session['username']
            # Fetch summary from database
        su = "SELECT * FROM summary WHERE user = %s"
        cursor.execute(su, (username,))
        summary1 = cursor.fetchall()
        print(summary1)
        return render_template("index.html", month=month, day=day, version=version, summary1=summary1)


# Login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']

        # Encode the encrypted email in base64
        email = username
        return redirect(url_for('login_password', email=email))
    else:
        return render_template("login.html")

# Signup


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        return redirect(url_for('set_password', email=email))
    else:
        return render_template('signup.html')

# setpassword


@app.route('/set_password', methods=['GET', 'POST'])
def set_password():

    email = request.args.get('email')
    if request.method == 'POST':
        password = request.form['password']
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = %s', (email,))
        result = cursor.fetchone()
        if result[0] == 1:
            flash('The user already exists.', 'error')
            return render_template('set_password.html', email=email)
        hashed_password = hashpw(password.encode('utf-8'), gensalt())
        cursor.execute(
            'INSERT INTO users (email, password) VALUES (%s, %s)', (email, hashed_password))
        cnx.commit()
        return redirect(url_for('verify', email=email))
    else:
        return render_template('set_password.html', email=email)


@app.route('/verify', methods=['GET', 'POST'])
def verify():

    email = request.args.get('email')
    # Generate verification code
    code = random.randint(100000, 999999)
    # Generate unique verification token
    token = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(days=5)
    # Check if email already has a verification record
    cursor.execute("SELECT * FROM verification WHERE email = %s", (email,))
    existing_record = cursor.fetchone()
    if existing_record:
        # Update existing verification record with new token, code, and expiration
        sql = "UPDATE verification SET token = %s, code = %s, expiration = %s WHERE email = %s"
        val = (token, code, expiration, email)
    else:
        # Insert new verification record
        sql = "INSERT INTO verification (email, token, code, expiration) VALUES (%s, %s, %s, %s)"
        val = (email, token, code, expiration)
    # Save token, email, and code to session with expiration time
    session['email'] = email
    session['code'] = code
    session['token'] = token
    session['expiration'] = expiration
    # Execute SQL query and commit changes
    cursor.execute(sql, val)
    cnx.commit()

    # Email content
    subject = 'Verify your email address'
    body = f'''<p>To continue setting up your OpenAI clone account, please verify that this is your email address.</p>
            <a href="{url_for("verifys", email=email, token=token, _external=True)}"><button style="background-color: #008CBA;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;">Verify email address</button></a>
            <p>This link will expire in 30 minutes. If you did not make this request, please disregard this email. 
            For help, contact us through our <a href="https://help.example.com/">Help center</a>.</p>'''

    msg = MIMEMultipart()
    msg['From'] = 'noreply@cyberride.com.ng'
    msg['To'] = email
    msg['Subject'] = subject
    # Add body to message
    msg.attach(MIMEText(body, 'html'))
    try:
        # Send email
        # Connect to SMTP server
        smtp_server = smtplib.SMTP('cyberride.com.ng', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        # Login to SMTP server
        smtp_server.login('noreply@cyberride.com.ng', 'heritech@098')
        # Send email
        smtp_server.sendmail('noreply@cyberride.com.ng',
                             email, msg.as_string())
        print('Email sent successfully!')
        return render_template('verify.html',  email=email)
    except Exception as e:
        print('Error sending email:', e)
        return render_template('verify.html',  email=email)
    finally:
        # Close SMTP server connection
        smtp_server.quit()
    return render_template('verify.html', email=email)


@app.route('/verify<token>')
def verifys(token):

    email = request.args.get('email')
    # Fetch verification info from the database
    cursor.execute(
        "SELECT code, expiration FROM verification WHERE email = %s AND token = %s", (email, token))
    result = cursor.fetchone()
    if result is None:
        return redirect(url_for('invalidtoken', email=email))
    code = result[0]
    expiration = result[1]

    # Check if code has expired (30-minute expiration time)
    if datetime.now() > expiration:
        return redirect(url_for('invalidtoken', email=email))

    # Check if the user has already been verified
    cursor.execute("SELECT is_verified FROM users WHERE email = %s", (email,))
    is_verified = cursor.fetchone()[0]
    if is_verified:
        return redirect(url_for('verified', email=email))

    # Update user table to set is_verified to 1
    cursor.execute(
        "UPDATE users SET is_verified = 1 WHERE email = %s", (email,))
    cnx.commit()

    # Email and code verification successful
    return render_template('onboardingphone.html', email=email)


@app.route('/verified')
def verified():
    email = request.args.get('email')
    return render_template('verified.html', email=email)


@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if request.method == 'POST':

        email = request.args.get('email')
        fname = request.form['fname']
        lname = request.form['lname']
        # Update the user's first name and last name in the database
        query = "UPDATE users SET first_name = %s, last_name = %s WHERE email = %s"
        cursor.execute(query, (fname, lname, email,))
        cnx.commit()
        return redirect(url_for('login'))

    return render_template('onboarding.html')


@app.route('/invalidtoken')
def invalidtoken():
    email = request.args.get('email')
    return render_template('invalid_token.html', email=email)

# resend code


@app.route('/resend_code/<email>')
def resend_code(email):

    email = request.args.get('email')
    # Generate new verification code and update verification record
    code = random.randint(100000, 999999)
    token = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(days=5)
    sql = "UPDATE verification SET token = %s, code = %s, expiration = %s WHERE email = %s"
    val = (token, code, expiration, email)
    cursor.execute(sql, val)
    cnx.commit()

    # Update session with new code and expiration time
    session['code'] = code
    session['expiration'] = expiration
    # Email content
    subject = 'Verify your email address'
    body = f'''<p>To continue setting up your OpenAI clone account, please verify that this is your email address.</p>
            <a href="{url_for("verifys", email=email, token=token, _external=True)}"><button style="background-color: #008CBA;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;">Verify email address</button></a>
            <p>This link will expire in 30 minutes. If you did not make this request, please disregard this email. 
            For help, contact us through our <a href="https://help.example.com/">Help center</a>.</p>'''

    msg = MIMEMultipart()
    msg['From'] = 'noreply@cyberride.com.ng'
    msg['To'] = email
    msg['Subject'] = subject
    # Add body to message
    msg.attach(MIMEText(body, 'html'))
    try:
        # Send email
        # Connect to SMTP server
        smtp_server = smtplib.SMTP('cyberride.com.ng', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        # Login to SMTP server
        smtp_server.login('noreply@cyberride.com.ng', 'heritech@098')
        # Send email
        smtp_server.sendmail('noreply@cyberride.com.ng',
                             email, msg.as_string())
        flash('Email sent')
        return render_template('verifys_sent.html',  email=email)
    except Exception as e:
        flash('Error sending email:', e)
        return render_template('verify.html',  email=email)
    finally:
        # Close SMTP server connection
        smtp_server.quit()
    # Redirect to verify page with encoded email
    return render_template('verifys_sent.html', email=email)


@app.route('/login_password', methods=['GET', 'POST'])
def login_password():
    is_logged_in = False
    username = ''  # Define a default value for username
    if 'username' in session:
        is_logged_in = True

        email = request.args.get('email')
        username = email
    error = ''
    email = request.args.get('email')
    username = email
    if request.method == 'POST':
        password = request.form['password'].encode('utf-8')
        cursor.execute("SELECT * FROM users WHERE email = %s", (username,))
        user = cursor.fetchone()
        if not user:
            flash('Invalid email', 'error')
            error = 'Invalid email'
            return render_template('login_password.html', username=username, is_logged_in=is_logged_in, error=error)
        hashed_password = user[2].encode('utf-8')
        if not checkpw(password, hashed_password):
            flash('Invalid email or password', 'error')
            error = 'Invalid email or password'
            return render_template('login_password.html', username=username, is_logged_in=is_logged_in, error=error)

        if user[4] == 1:  # user is verified
            session['logged_in'] = True
            session['username'] = user[1]
            session['id'] = user[0]
            return redirect(url_for('index'))
        else:  # user is not verified
            return redirect(url_for('verify', email=email))

    return render_template('login_password.html', username=username, is_logged_in=is_logged_in, error=error)


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    if session.get('was_once_logged_in'):
        del session['was_once_logged_in']
    response = make_response(redirect('/'))
    response.delete_cookie('remember_token')
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    theme = request.form.get('theme', 'light')
    if request.method == 'POST':
        if theme == 'light':
            theme = 'dark'
        else:
            theme = 'light'
    return render_template('dashboard.html', theme=theme)


@app.route('/b', methods=['POST', 'GET'])
def b():
    theme = request.form.get('theme', 'light')
    if request.method == 'POST':
        if theme == 'light':
            theme = 'dark'
        else:
            theme = 'light'
    print(theme)
    return render_template('b.html', theme=theme)


@app.route("/google/login")
def google_login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/google/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Check if the user already exists in the database
    query = "SELECT id FROM users WHERE email=%s"
    cursor.execute(query, (users_email,))
    result = cursor.fetchone()

    if result:
        # User already exists in the database
        # username= result[0]
        sql = "UPDATE users SET picture = %s WHERE email = %s"
        val = (picture, users_email)
    else:
        password = generate_password()
        sql = "INSERT INTO users ( first_name, email, password, picture, is_verified) VALUES ( %s, %s, %s, %s, %s)"
        val = (users_name, users_email, password, picture, 1)
    print(unique_id)
    cursor.execute(sql, val)
    cnx.commit()
    # Save the user ID in the session
    session['username'] = users_email
    # Redirect to the home page
    return redirect(url_for('index'))

@app.route("/new-chat", methods=["GET", "POST"])
def new_chat():
    username = session['username']
    # Fetch summary from database
    su = "SELECT * FROM summary WHERE user = %s"
    cursor.execute(su, (username,))
    summary1 = cursor.fetchall()
    conversation_id = str(uuid.uuid4())
    # Store the new conversation ID in the session object
    session['conversation_id'] = conversation_id
    
    sql = "SELECT picture FROM users WHERE email = %s"
    cursor.execute(sql, (username,))
    img = cursor.fetchone()
    summ = ""
    # Retrieve conversation ID from query parameter or session object
    conversation_id = request.args.get('conversation_id')
    if not conversation_id:
        conversation_id = session.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            session['conversation_id'] = conversation_id

    # # Check if conversation ID is already stored in session object
    # if 'conversation_id' not in session:
    #     session['conversation_id'] = str(uuid.uuid4())

    if request.method == 'POST':
        # Retrieve conversation ID from session object
        conversation_id = session['conversation_id']

        # Handle user input
        user_input = request.form['user-input']

        # Get conversation history from the database
        cursor.execute(
            "SELECT input, output FROM chat WHERE user = %s AND conversation_id = %s", (username, conversation_id))
        results = cursor.fetchall()
        conversation = []
        for input_, output in results:
            conversation.append({"user": input_, "bot": output})
        
        # If there is no history for the conversation, generate a summary for the first input
        if not conversation:
            global processed_first_input
            if not processed_first_input:
                # Call OpenAI API to generate summary
                summary = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=f"Summarize this:\n\n{user_input}",
                    temperature=0.7,
                    max_tokens=5,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                # Extract summary text from API response
                summ = summary.choices[0].text.strip()
                # Set flag variable to True
                processed_first_input = True
                # Insert summary into the database
                cursor.execute(
                    'INSERT INTO summary (user, conversation_id, summary) VALUES (%s, %s, %s)',  (username, conversation_id, summ))
                cnx.commit()
            else:
                summ = ""
        else:
            # Retrieve the summary from the database
            cursor.execute(
                "SELECT summary FROM summary WHERE user = %s AND conversation_id = %s", (username, conversation_id))
            result = cursor.fetchall()
            summ = result[0] if result else ""

        # Call OpenAI API to generate response
        start_sequence = "\nAI:"
        restart_sequence = "\nHuman: "

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=user_input,
            temperature=0.9,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0.16,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        # Extract response text from API response
        output = response.choices[0].text.strip()

        # Insert user input and bot response into the database
        cursor.execute('INSERT INTO chat (user, conversation_id, input, output) VALUES (%s, %s, %s, %s)',
                       (username, conversation_id, user_input, output))
        cnx.commit()

        # Add the latest input and response to the conversation history
        conversation.append({"user": user_input, "bot": output})

    else:
        # Handle GET request
        conversation = []
    print(summary1)
    return render_template("chat.html", conversation=conversation, img=img, summ=summ, summary1= summary1)

@app.route("/chat", methods=["GET", "POST"])
def chat():
    username = session['username']
    # Fetch summary from database
    su = "SELECT * FROM summary WHERE user = %s"
    cursor.execute(su, (username,))
    summary1 = cursor.fetchall()

    sql = "SELECT picture FROM users WHERE email = %s"
    cursor.execute(sql, (username,))
    img = cursor.fetchone()
    
    summ = ""

    # Retrieve conversation ID from query parameter or session object
    conversation_id = request.args.get('conversation_id')
    if not conversation_id:
        conversation_id = session.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            session['conversation_id'] = conversation_id

    # # Check if conversation ID is already stored in session object
    # if 'conversation_id' not in session:
    #     session['conversation_id'] = str(uuid.uuid4())

    if request.method == 'POST':
        # Retrieve conversation ID from session object
        conversation_id = session['conversation_id']

        # Handle user input
        user_input = request.form['user-input']

        # Get conversation history from the database
        cursor.execute(
            "SELECT input, output FROM chat WHERE user = %s AND conversation_id = %s", (username, conversation_id))
        results = cursor.fetchall()
        conversation = []
        for input_, output in results:
            conversation.append({"user": input_, "bot": output})
        
        # If there is no history for the conversation, generate a summary for the first input
        if not conversation:
            global processed_first_input
            if not processed_first_input:
                # Call OpenAI API to generate summary
                summary = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=f"Summarize this:\n\n{user_input}",
                    temperature=0.7,
                    max_tokens=5,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                # Extract summary text from API response
                summ = summary.choices[0].text.strip()
                # Set flag variable to True
                processed_first_input = True
                # Insert summary into the database
                cursor.execute(
                    'INSERT INTO summary (user, conversation_id, summary) VALUES (%s, %s, %s)',  (username, conversation_id, summ))
                cnx.commit()
            else:
                summ = ""
        else:
            # Retrieve the summary from the database
            cursor.execute("SELECT summary FROM summary WHERE user = %s AND conversation_id = %s", (username, conversation_id))
            result = cursor.fetchall()
            summ = result[0][0] if result else ""


        # Call OpenAI API to generate response
        start_sequence = "\nAI:"
        restart_sequence = "\nHuman: "

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=user_input,
            temperature=0.9,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0.16,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        # Extract response text from API response
        output = response.choices[0].text.strip()

        # Insert user input and bot response into the database
        cursor.execute('INSERT INTO chat (user, conversation_id, input, output) VALUES (%s, %s, %s, %s)',
                       (username, conversation_id, user_input, output))
        cnx.commit()

        # Add the latest input and response to the conversation history
        conversation.append({"user": user_input, "bot": output})

    else:
        # Handle GET request
        conversation = []

    return render_template("chat.html", conversation=conversation, img=img, summ=summ, summary1= summary1)
@app.route('/chat/<conversation_id>')
def conversation(conversation_id):
    username = session['username']
    su = "SELECT * FROM summary WHERE user = %s"
    cursor.execute(su, (username,))
    summary1 = cursor.fetchall()
    # Retrieve conversation history from the database
    sql = "SELECT picture FROM users WHERE email = %s"
    cursor.execute(sql, (username,))
    img = cursor.fetchone()
        # Retrieve the summary from the database
    cursor.execute("SELECT summary FROM summary WHERE user = %s AND conversation_id = %s", (username, conversation_id))
    result = cursor.fetchall()
    summ = result[0][0] if result else ""
    cursor.execute("SELECT input, output FROM chat WHERE conversation_id = %s", (conversation_id,))
    results = cursor.fetchall()
    conversation = []
    for input_, output in results:
        conversation.append({"user": input_, "bot": output})
        
    # Render the conversation template with the conversation history
    return render_template('chat.html', conversation=conversation, img=img, summ=summ, summary1=summary1)

# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))
