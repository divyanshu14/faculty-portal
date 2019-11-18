from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
import bcrypt
import psycopg2
from bson import json_util, ObjectId
import json
import datetime

load_dotenv()

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'faculty'
app.config["MONGO_URI"] = "mongodb://localhost:27017/faculty"

mongo = PyMongo(app)
users = mongo.db.profiles

connection = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_DATABASE"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
)
cursor = connection.cursor()

def isempty(str):
    if str.isspace() or not str:
        return True
    return False


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route('/requestleave', methods=['POST', 'GET'])
def requestleave():
    if request.form :
        if request.form['days'].isnumeric() and int(request.form['days'])>0 :
            cursor.execute("call launch_new_leave_application('" + session['emailid'] + "', " + str(int(request.form['days'])) + ", '" + request.form['message'] + "')")
    return render_template('newleave.html')


@app.route('/login', methods=['POST'])
def login():
    if(request.form):
        # login_user = users.find_one({'emailid': request.form['emailid']})
        cursor.execute("select * from all_email where '" + request.form['emailid'] + "' = email")
        temp = cursor.fetchone()
        print(temp)
        if temp == None:
            return render_template('login.html',msg = 'Emailid not registered')
        employee_type = temp[1]

        if employee_type == 'fac': # validate password and get emp_id
            cursor.execute("select * from faculty where '" + request.form['emailid'] + "' = fac_email AND password = crypt('" + request.form['password'] + "',password)")
        
        elif employee_type == 'cc_fac':
            cursor.execute("select * from cc_faculty where '" + request.form['emailid'] + "' = cc_fac_post_email AND password = crypt('" + request.form['password'] + "',password)")
        
        elif employee_type == 'hod':
            cursor.execute("select * from hod where '" + request.form['emailid'] + "' = hod_post_email AND password = crypt('" + request.form['password'] + "',password)")
        
        temp = cursor.fetchone()
        print(temp)
        if temp == None:
            return render_template('login.html', msg = 'Invalid credentials')
        # store the login position details in session as session['login_user']
        session['login_user'] = temp
        session['emailid'] = request.form['emailid']
        # employee details includes employee
        if employee_type == 'fac':
            cursor.execute("select * from employee where emp_id = " + str(temp[2]))
            session['emp_details'] = cursor.fetchone()

        elif employee_type == 'cc_fac':
            cursor.execute("select * from employee where emp_id = " + str(temp[3]))
            session['emp_details'] = cursor.fetchone()

        elif employee_type == 'hod':
            cursor.execute("select fac_emp_id from faculty where fac_email = '" + temp[2] + "'")
            val = cursor.fetchone()[0]
            cursor.execute("select * from employee where emp_id = " + str(val))
            session['emp_details'] = cursor.fetchone()

        print(session['emp_details'])
        # now connect to mongodb profile of this employee
        user_profile = users.find_one({'emp_id': session['emp_details'][0]})
        cursor.execute("select * from rem_leaves where emp_id = " + str(session['emp_details'][0]))
        leaves_list = cursor.fetchall()
        if len(leaves_list) == 0:
            ltuple = (session['emp_details'][0],datetime.datetime.now().year,20)
            leaves_list.insert(0,ltuple)
        return render_template('viewdashboard.html', user = user_profile, leaves = leaves_list) 
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/editprofile', methods=['POST', 'GET'])
def editprofile():
    if request.method == 'POST':
        for fieldname in request.form:
            users.update({'emp_id': session['emp_details'][0]},{"$set": {fieldname: request.form[fieldname]}})
        return render_template('viewdashboard.html', user = users.find_one({'emp_id': session['emp_details'][0]}))
    return render_template('editprofile.html', user = users.find_one({'emp_id': session['emp_details'][0]}))

@app.route('/adddetails', methods=['POST', 'GET'])
def adddetails():
    if request.method == 'POST':
        users.update({'emp_id': session['emp_details'][0]},{"$set": {request.form['newfield']: request.form['newvalue']}})
        return render_template('editprofile.html', user = users.find_one({'emp_id': session['emp_details'][0]}))
    return render_template('adddetails.html')


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)