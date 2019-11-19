from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
import bcrypt
import psycopg2
from bson import json_util, ObjectId
import json

load_dotenv()

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'faculty'
app.config["MONGO_URI"] = "mongodb://localhost:27017/faculty"

mongo = PyMongo(app)
users = mongo.db.profiles
# connection = psycopg2.connect(
#         host=os.environ.get("DB_HOST"),
#         database=os.environ.get("DB_DATABASE"),
#         user=os.environ.get("DB_USER"),
#         password=os.environ.get("DB_PASSWORD")
# )
# cursor = connection.cursor()


@app.route('/', methods=['POST', 'GET'])
def index():
    if 'emailid' in session:
        return render_template('dashboard.html', user_details = session['login_user'])
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    login_user = users.find_one({'emailid': request.form['emailid']})

    if login_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['emailid'] = request.form['emailid']
            session['login_user'] = json.loads(json_util.dumps(login_user))
            return redirect(url_for('index'))
    
    return 'Invalid emailid/password combo!'



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # check if user already exists
        users = mongo.db.profiles
        existing_user = users.find_one({'emailid': request.form['emailid']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'emailid': request.form['emailid'], 'password' : hashpass})
            session['emailid'] = request.form['emailid']
            login_user = users.find_one({'emailid': request.form['emailid']})
            session['login_user'] = json.loads(json_util.dumps(login_user))
            return redirect(url_for('index'))
        
        flash('Account already exists')
        return redirect(url_for('index'))
    
    return render_template('register.html')
        

        

@app.route('/logout')
def logout():
    session.clear()
    return index()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)