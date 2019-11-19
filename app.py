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

app.config["MONGO_URI"] = "mongodb://localhost:27017/" + os.environ.get("MONGO_DBNAME")

mongo = PyMongo(app)
users = mongo.db.profiles

connection = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_DATABASE"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
)
connection.autocommit = True
cursor = connection.cursor()


def get_finished_status():
    cursor.execute("select * from approved_or_rejected_leave_application where launched_by_emp_id = " + str(session['emp_details'][0]))
    return cursor.fetchall()



def get_pending_requests():
    cursor.execute("select * from curr_leave_application where curr_holder_email = '" + session['emailid']  + "'")
    temp = cursor.fetchall()
    # print(temp)
    temp_list = []
    for row in temp:
        # print("---------------------------------------")
        # print(row)
        cursor.execute("select * from can_approve_or_reject(" + str(row[0]) + ")")
        temp_list.append(list(row))
        temp_list[-1].append(cursor.fetchone()[0])
    # print  (temp_list)
    return temp_list



def get_my_application_status():
    cursor.execute("select * from curr_leave_application where launched_by_emp_id = " + str(session['emp_details'][0]))
    return cursor.fetchall()



def isempty(str):
    if str.isspace() or not str:
        return True
    return False



def get_leaves_list():
    cursor.execute("select * from rem_leaves where emp_id = " + str(session['emp_details'][0]))
    leaves_list = cursor.fetchall()
    if len(leaves_list) == 0:
        ltuple = (session['emp_details'][0],datetime.datetime.now().year,20)
        leaves_list.insert(0,ltuple)
    return leaves_list



@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html',users = users.find({}))


@app.route('/viewfaculty/<string:id>', methods=['POST', 'GET'])
def viewuser(id):
    id = int(id)
    return render_template('viewfaculty.html', user =users.find_one({'emp_id': id}) )


@app.route('/viewdashboard', methods=['POST','GET'])
def viewdashboard():
    user_profile = users.find_one({'emp_id': session['emp_details'][0]})
    return render_template('viewdashboard.html', user = user_profile, finished_applications = get_finished_status(),
    rem_leaves = get_leaves_list(), app_status = get_my_application_status(), pending_requests = get_pending_requests()) 



@app.route('/requestleave', methods=['POST', 'GET'])
def requestleave():
    if request.form :
        if request.form['days'].isnumeric() and int(request.form['days'])>0 :
            cursor.execute("call launch_new_leave_application('" + session['emailid'] + "', " + str(int(request.form['days'])) + ", '" + request.form['message'] + "')")
    return render_template('newleave.html')


@app.route('/login', methods=['POST','GET'])
def login():
    # if request.method = 'GET':
    #     return redirect(url_for('login'))
    if request.form :
        # login_user = users.find_one({'emailid': request.form['emailid']})
        cursor.execute("select * from all_email where '" + request.form['emailid'] + "' = email")
        temp = cursor.fetchone()
        print(temp)
        if temp == None:
            return render_template('login.html',msg = 'Emailid not registered')
        employee_type = temp[1]

        cursor.execute("select current_date")
        curr_date = cursor.fetchone()

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
            if curr_date[0] > session['login_user'][5]:
                return "Your tenure has ended! Contact Admin."
            cursor.execute("select * from employee where emp_id = " + str(temp[3]))
            session['emp_details'] = cursor.fetchone()

        elif employee_type == 'hod':
            if curr_date[0] > session['login_user'][4]:
                return "Your tenure has ended! Contact Admin."
            cursor.execute("select fac_emp_id from faculty where fac_email = '" + temp[2] + "'")
            val = cursor.fetchone()[0]
            cursor.execute("select * from employee where emp_id = " + str(val))
            session['emp_details'] = cursor.fetchone()

        print(session['emp_details'])
        # now connect to mongodb profile of this employee
        return redirect(url_for('viewdashboard'))
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
        return redirect(url_for('viewdashboard'))
    return render_template('editprofile.html', user = users.find_one({'emp_id': session['emp_details'][0]}))



@app.route('/adddetails', methods=['POST', 'GET'])
def adddetails():
    if request.method == 'POST':
        users.update({'emp_id': session['emp_details'][0]},{"$set": {request.form['newfield']: request.form['newvalue']}})
        return render_template('editprofile.html', user = users.find_one({'emp_id': session['emp_details'][0]}))
    return render_template('adddetails.html')



@app.route('/newapplication', methods=['POST','GET'])
def newapplication():
    if request.method == 'POST':
        if request.form['days'].isnumeric():
            days = int(request.form['days'])
            if days>0 :
                req = ("call launch_new_leave_application('" + session['emailid'] + "', " + str(days) + ", '" + request.form['comment'] + "');")
                try:
                    cursor.execute(req)
                except:
                    redirect(url_for('viewdashboard'))
        else:
            return 'Invalid input given'
    return redirect(url_for('viewdashboard'))



@app.route('/applicationdetails/<string:id>', methods=['POST','GET'])
def applicationdetails(id):
    cursor.execute("select * from application_detail where app_id = " + id)
    det = cursor.fetchall()
    print(det)
    return render_template('papertrail.html', details = det)



@app.route('/forwardapplication/<string:id>', methods=['POST','GET'])
def forwardapplication(id):
    cursor.execute("select * from can_approve_or_reject(" + id + ")")
    val = cursor.fetchone()[0]
    print(val)
    if val:
        cursor.execute("call approve_or_reject(" + id + ", true, '" + request.form['comment'] + "')")
    else:
        cursor.execute("call forward(" + id + ", '" + request.form['comment'] + "')")
    return redirect(url_for('viewdashboard'))



@app.route('/returnapplication/<string:id>', methods=['POST','GET'])
def returnapplication(id):
    # cursor.execute("select * from can_approve_or_reject(" + id + ")")
    # val = cursor.fetchone()[0]
    # print(val)
    # if val:
    #     cursor.execute("call approve_or_reject(" + id + ", false, '" + request.form['comment'] + "')")
    # else:
    cursor.execute("call send_back_to_owner_for_more_comments(" + id + ", '" + request.form['comment'] + "')")
    return redirect(url_for('viewdashboard'))


@app.route('/rejectapplication/<string:id>', methods=['POST','GET'])
def rejectapplication(id):
    cursor.execute("call approve_or_reject(" + id + ", false, '" + request.form['comment'] + "')")
    return redirect(url_for('viewdashboard'))

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)