from flask import Flask, render_template, request, make_response, session, escape
from flask_wtf.csrf import CSRFProtect
from subprocess import check_output
import os
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


INPUTTEXT_ADDR = 'input.txt'
DICTIONARY_ADDR = 'wordlist.txt'
SECRET_KEY = os.urandom(32)
DATABASE_FILE = "sqlite:///" + os.path.join(os.getcwd(), "database.db")

users = []

def getUser(username):
    return UserRecord.query.filter_by(username=username).first()

app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config.update(SQLALCHEMY_DATABASE_URI = DATABASE_FILE)
app.config.update(SQLALCHEMY_TRACK_MODIFICATIONS = False)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)

class UserRecord(db.Model):
    __tablename__ = "user_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    phone = db.Column(db.String(64))

class LoginRecord(db.Model):
    __tablename__ = "login_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64))
    login_time = db.Column(db.DateTime)
    logout_time = db.Column(db.DateTime)

class SpellCheckRecord(db.Model):
    __tablename__ = "spell_check_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64))
    inputtext = db.Column(db.String(64))
    misspelled = db.Column(db.String(64))

db.create_all()

@app.route('/')
def index():
    return redirect('register')

@app.route('/spell_check', methods=['GET', 'POST'])
def spell_check():
    textout = None
    misspelled = None
    if (request.method == 'POST'):
        if 'username' in session:
            username = session['username']
            user = getUser(username)
        else:
            user = None
        if user:
            inputtext = request.form['inputtext']
            inputtext_file = open(INPUTTEXT_ADDR, 'w')
            inputtext_file.write(inputtext)
            inputtext_file.close()
            textout=inputtext
            misspelled = check_output(['./a.out', INPUTTEXT_ADDR, DICTIONARY_ADDR]).decode('utf-8')
            misspelled = misspelled.replace('\n', ',').strip(',')
            spell_check_record = SpellCheckRecord(username=user.username, inputtext=inputtext, misspelled=misspelled)
            db.session.add(spell_check_record)
            db.session.commit()
        else:
            textout = "Invalid user. Please log in."
    response = make_response(render_template('spell_check.html', textout=textout, misspelled=misspelled))
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("log in function")
    error = None
    if (request.method == 'POST'):
        username = escape(request.form['uname'])
        password = escape(request.form['pword'])
        phone = escape(request.form['2fa'])
        if not username:
            error = 'invalid username'
        elif not password:
            error = 'invalid password'
        elif not phone:
            error = 'invalid phone'
        else:
            user = getUser(username)
            if not user:
                error = 'Incorrect'
            elif (not sha256_crypt.verify(password, user.password)):
                error = 'Incorrect'
            elif (not phone == user.phone):
                error = 'Two-factor failure'
            else:
                error = 'success'
                session['username'] = username
                session['user_id'] = user.id
                login = LoginRecord(username=username, login_time=datetime.utcnow())
                db.session.add(login)
                db.session.commit()
    response = make_response(render_template('login.html', error=error))
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if (request.method == 'POST'):
        username = escape(request.form['uname'])
        password = escape(request.form['pword'])
        phone = escape(request.form['2fa'])
        if not username:
            error = 'invalid username'
        elif not password:
            error = 'invalid password'
        elif not phone:
            error = 'invalid phone'
        else:
            if not getUser(username):
                user = UserRecord(username=username, password=sha256_crypt.hash(password), phone=phone)
                db.session.add(user)
                db.session.commit()
                error = 'success'
            else:
                error = 'failure'
    response = make_response(render_template('register.html', error=error))
    return response

@app.route('/history', methods=['GET', 'POST'])
def history():
    admin = False
    if 'username' in session:
        username = session['username']
        user = getUser(username)
        if not user:
            return login()
        if username == 'admin':
            admin = True
    else:
        return login()
    if (request.method == 'POST') and admin:
        userquery = request.form['userquery']
        spell_check_records = SpellCheckRecord.query.filter_by(username=userquery).order_by(SpellCheckRecord.id)
    elif admin:
        spell_check_records = SpellCheckRecord.query.order_by(SpellCheckRecord.id)
    else:
        spell_check_records = SpellCheckRecord.query.filter_by(username=user.username).order_by(SpellCheckRecord.id)
    records_as_html = ''
    number_of_records = 0
    for record in spell_check_records:
        number_of_records += 1
    history_records = open('templates/history_records.html', 'w')
    history_records.write(records_as_html)
    history_records.close()
    response = make_response(render_template('history.html', records=spell_check_records, number_of_records=number_of_records, admin=admin))
    return response

@app.route('/history/query<int:id>')
def query(id):
    if 'username' in session:
        username = session['username']
        user = getUser(username)
        record = SpellCheckRecord.query.filter_by(id=id).first()
        if username == 'admin' or record.username == username:
            response = make_response(render_template('record_by_id.html', id=id, username=record.username, inputtext=record.inputtext, misspelled=record.misspelled))
            return response
    return login()

@app.route('/login_history', methods=['GET', 'POST'])
def login_history():
    records = {}
    admin = False
    if 'username' in session and session['username'] == 'admin':
        admin = True
    if request.method == 'POST' and admin:
        userid = request.form['userid']
        records = LoginRecord.query.filter_by(username=userid).order_by(LoginRecord.id)
    response = make_response(render_template('login_history.html', admin=admin, records=records))
    return response

if (__name__ == '__main__'):
    app.run(debug=True)
