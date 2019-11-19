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
app.config["MONGO_URI"] = "mongodb://localhost:27017/" + os.environ.get("MONGO_DBNAME2")

mongo = PyMongo(app)
users = mongo.db.profiles

connection = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_DATABASE2"),
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
    return render_template('adminindex.html', users = users.find({}))


@app.route('/viewfaculty/<string:id>', methods=['POST', 'GET'])
def viewuser(id):
    id = int(id)
    return render_template('viewfaculty.html', user =users.find_one({'emp_id': id}) )

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
        users.insert({'emp_id': emp_id, 'name': request.form['name'], 'department': request.form['dep_name']})
        return 'Done'
    return render_template('registerfac.html')


@app.route('/createhod', methods=['POST','GET'])
def createhod():
    if request.form:
        if isempty(request.form['facemailid']) or isempty(request.form['password']) or isempty(request.form['hodemailid']) or isempty(request.form['end_date']) :
            return 'Fields cannot be empty!'
        # try:
        cursor.execute("insert into hod(hod_post_email,hod_fac_email,hod_end_date,password) values ('" 
        + request.form['hodemailid'] + "', '" + request.form['facemailid'] + "', '" + request.form['end_date'] + "', crypt('" + request.form['password'] + "', gen_salt('bf')));")
        connection.commit();
        return redirect(url_for('adminindex'))
        # except:
        #     return "Error with the request!"
    return render_template('makehod.html')



@app.route('/hod', methods=['POST','GET'])
def hod():
    if request.form:
        if isempty(request.form['fac_email']) or isempty(request.form['end_date']) :
            return 'Fields cannot be empty!'
        cursor.execute("select fac_dep_name from faculty where fac_email = '" + request.form['fac_email'] + "'")
        dept = cursor.fetchone()[0]
        cursor.execute("select fac_email from faculty where fac_dep_name = '" + dept+ "' and fac_email = any(select hod_fac_email from hod)")
        oldhod_fac_email = cursor.fetchone()
        if not oldhod_fac_email:
            return render_template('createhod.html')
        req = "select * from change_hod('" + request.form['post_email'] + "', '" + request.form['fac_email'] + "', '" + request.form['start_date'] + "', '" + request.form['end_date'] + "')"
        cursor.execute(req)
        connection.commit()
        # try:
        # cursor.execute("select fac_dep_name from faculty where fac_email = '" + request.form['facemailid'] + "'")
        # dept = cursor.fetchone()[0]
        # cursor.execute("select fac_email from faculty where fac_dep_name = '" + dept+ "' and fac_email = any(select hod_fac_email from hod)")
        # oldhod_fac_email = cursor.fetchone()
        # if not oldhod_fac_email:
        #     return render_template('createhod.html')
        # cursor.execute("update hod set hod_fac_email = '" + request.form['facemailid'] + "', hod_end_date = '" + request.form['end_date'] + "' where hod_fac_email = '" + oldhod_fac_email[0] + "'")
        # connection.commit();
        return redirect(url_for('adminindex'))
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
        try:
            cursor.execute("insert into cc_faculty(cc_fac_post_email,cc_fac_post, cc_fac_emp_id,cc_fac_end_date,password) values ('" + request.form['emailid'] + "', '" + request.form['position'] + "', " + str(emp_id) + ", '" + request.form['end_date'] + "', crypt('" + request.form['password'] + "', gen_salt('bf')));")
            users.insert({'emp_id': emp_id, 'name': request.form['name']})
        except:
            print('a')
        req = "select * from change_cc_faculty('" + request.form['position'] + "', " + str(emp_id) + ", '" + request.form['start_date'] + "', '" + request.form['end_date']+ "');"
        print(req)
        cursor.execute(req)
        users.insert({'emp_id': emp_id, 'name': request.form['name']})
        connection.commit()
        return 'Done. But password remains same as previous postholder.'
    return render_template('registerccfac.html')

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=8000, debug=True)
# if __name__ == "__main__":
    
    # app.run(debug=True)