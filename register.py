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

@app.route('/', methods=['POST','GET'])
def adminindex():
    return render_template('adminindex.html')


# form for creating new employee with entries of emp_name, dep_type, emailid, password
@app.route('/faculty', methods=['POST','GET'])
def faculty():
    if request.form :
        if isempty(request.form['emailid']) or isempty(request.form['password']) or isempty(request.form['name']) or isempty(request.form['dep_name']) :
            return 'Fields cannot be empty!'
        # create new employee in postgres
        cursor.execute("insert into employee(emp_name) values ('" + request.form['name'] + "')")
        cursor.execute("select max(emp_id) from employee")
        emp_id = cursor.fetchone()[0]
        # insert this employee id into mongodb
        # #  enter into faculty table'
        print(emp_id)
        cursor.execute("insert into faculty(fac_email,fac_emp_id,fac_dep_name,password) values ('" 
        + request.form['emailid'] + "', " + str(emp_id) + ", '" + request.form['dep_name'] + "', crypt('" + request.form['password'] + "', gen_salt('bf')))")
        connection.commit()
        users.insert({'emp_id': emp_id, 'name': request.form['name']})
        return 'Done'
    return render_template('registerfac.html')



@app.route('/hod', methods=['POST','GET'])
def hod():
    if request.form:
        a = 5
    return render_template('makehod.html')



@app.route('/ccfaculty', methods=['POST','GET'])
def ccfaculty():
    if request.form :
        if isempty(request.form['emailid']) or isempty(request.form['password']) or isempty(request.form['name']) or isempty(request.form['position']) :
            return 'Fields cannot be empty!'
        # create new employee in postgres
        cursor.execute("insert into employee(emp_name) values ('" + request.form['name'] + "')")
        cursor.execute("select max(emp_id) from employee")
        emp_id = cursor.fetchone()[0]
        # insert this employee id into mongodb
        # insert into cc_fac table
        cursor.execute("insert into cc_faculty(cc_fac_post_email,cc_fac_post, cc_fac_emp_id,cc_fac_end_date,password) values ('"
        + request.form['emailid'] + "', '" + request.form['position'] + "', " + str(emp_id) + ", '" + request.form['end_date'] + "', crypt('" + request.form['password'] + "', gen_salt('bf')));")
        connection.commit()
        users.insert({'emp_id': emp_id, 'name': request.form['name']})
        return 'Done'
    return render_template('registerccfac.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)