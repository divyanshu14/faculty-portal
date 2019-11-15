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
def isempty(str):
    if str.isspace() or not str:
        return True
    return False


@app.route('/', methods=['POST', 'GET'])
def index():
    if 'emailid' in session:
        return render_template('dashboard.html', user_details = session['login_user'])
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    if(request.form):
        login_user = users.find_one({'emailid': request.form['emailid']})
        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['emailid'] = request.form['emailid']
                session['login_user'] = json.loads(json_util.dumps(login_user))
                return redirect(url_for('index'))
            else:
                return render_template('login.html', msg = "Invalid emailid/password combo")
    return render_template('login.html')



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if isempty(request.form['emailid']) or isempty(request.form['password']):
            return 'Emailid and password cannot be empty!'
        # check if user already exists
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
    return redirect(url_for('index'))

@app.route('/editprofile', methods=['POST', 'GET'])
def editprofile():
    if request.method == 'POST':
        for fieldname in request.form:
            users.update({'emailid': session['emailid']},{"$set": {fieldname: request.form[fieldname]}})
        return render_template('dashboard.html', user_details = session['login_user'])
    return render_template('editprofile.html', user = users.find_one({'emailid': session['emailid']}))

@app.route('/adddetails', methods=['POST', 'GET'])
def adddetails():
    if request.method == 'POST':
        users.update({'emailid': session['emailid']},{"$set": {request.form['newfield']: request.form['newvalue']}})
        return render_template('editprofile.html', user = users.find_one({'emailid': session['emailid']}))
    return render_template('adddetails.html')


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)