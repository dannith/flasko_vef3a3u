import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from flask_mail import Mail, Message
from random import randint

#CONFIG
DATABASE = "sqlite.db"
DEBUG = False
SECRET_KEY = "vef3a3"
USERNAME = "admin"
PASSWORD = "default"
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'klippilokaverk@gmail.com'
MAIL_PASSWORD = "klipping"

#App
app = Flask(__name__)
app.config.from_object(__name__)

#Mail
mail = Mail(app)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

def get_connection():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = connect_db()
    return db

def query_db(query, args=(), one=False):
    db = get_connection()
    cur = db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def insert(table, fields=(), values=()):
    # g.db is the database connection
    cur = g.db.cursor()
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
    )
    cur.execute(query, values)
    g.db.commit()
    id = cur.lastrowid
    cur.close()
    return id

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    posts = query_db("SELECT * FROM get_posts_info ORDER BY id desc")
    return render_template("home.html", posts = posts)

@app.route('/posts/')
@app.route('/posts/<int:id>', methods = ['GET', 'POST'])
def posts(id = None):
    if request.method == 'POST':
        try:
            if session['id']:
                insert('comments', ['text', 'author_id', 'post_id'], [request.form['comment'], session['id'], id])
                flash('Comment successful!')
        except: redirect(url_for('login'))
    if not id:
        return redirect(url_for('index'))
    postinfo = query_db("select * from get_posts_info where id = ?", [id], True) #Skilar None ef ekkert finnst
    if postinfo:
        comments = query_db("SELECT * FROM get_comments where post_id = ?", [postinfo['id']])
        return render_template('posts.html', postinfo = postinfo, comments = comments)
    if not postinfo:
       return redirect(url_for('index'))

@app.route('/posts/create', methods=['GET', 'POST'])
def createPost():
    if 'id' not in session:
        flash('Please log in to view this page.')
        return redirect(url_for('login'))
    titleError = None
    textError = None
    if request.method == 'POST':
        pTitle = request.form["ptitle"]
        pText = request.form["ptext"]
        pCmtbl = request.form["pcommentable"]
        if not pTitle: titleError = True    #   EMPTY FORMS:
        if not pText: textError = True      #   Indicate errors
        if not titleError and not textError:
            insert("posts", ['title', 'text', 'commentable', 'author_id'], [pTitle, pText, pCmtbl, session['id']])
            flash("Post successfull! Scroll down to view.")
            return redirect(url_for('index'))
    return render_template('create.html', titleError = titleError, textError = textError)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    error = False
    emailError = False
    usernameError = False
    if request.method == 'POST':
        #query db hjálparfall sem er gert f ofan, True (skila einni row)
        if query_db("select username from users where username = ?", [request.form['username']], True):
            usernameError = "Invalid Username"
            error = True
        if query_db("select username from users where email = ?", [request.form['email']], True):
            emailError = "Invalid email"
            error = True
        if len(request.form['username']) > 20:
            usernameError = "Username too long."
            error = True
        if error != True:
            insert("users", ["username", "pword", "email", "status", "rank"], [request.form['username'], request.form['password'], request.form['email'], 4, 1])
            return redirect(url_for('index'))
    return render_template("register.html", error=error, usernameError=usernameError, emailError = emailError)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in session:
        flash('Already logged in.')
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        user = query_db("select id, rank from users where username = ? and pword = ?",[request.form['username'], request.form['password']], True)
        if user != None:
            session['id'] = user['id']
            print(user['rank'])
            if user['rank'] == 3:
                session['admin'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
        else:
            error = "Incorrect username or password."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'id' in session:
        session.pop('id', None)
        session.pop('admin', None)
        flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/appointments/')
def appointments():
    return redirect(url_for('index'))
@app.route('/appointments/book', methods = ['GET', 'POST'])
def book():
    if 'id' not in session:
        flash('Please login to view this page.')
        return redirect(url_for('login'))
    hairerror = None
    treaterror = None
    if request.method == "POST":
        # Ok hef ekki hugmynd afhverju en stundum þarf ég að gera try/catch á request form því það kemur proxy error annars:
        #   (Getur kíkt á /posts/create, þar þurftu ég ekki að gera try/catch)
        try: request.form['hairdresser']
        except: hairerror = True
        try: request.form['treatment']
        except: treaterror = True
        if not hairerror and not treaterror:
            key = randint(1000, 10000) # "Lykillinn" sem fer á url eftir /confirm/LYKILL til þess að staðfesta tímann, ekkert of sniðugt að hafa 10000 int þar sem einhver gæti gert for loopu og confirmað allt (betra að bæta smá bókstöfum inn í)

            x = insert("appointments", ["type", "comment", "customer_id", "hairdresser_id"], [request.form['treatment'], request.form['comment'], session['id'], request.form['hairdresser']]) #x = id á nýjustu röð í table
            insert("confirmations", ["key", "appointment_id"], [key, x])
            hdresser = query_db("SELECT username FROM users WHERE id = ?", [request.form['hairdresser']], True)
            tmeant = query_db("SELECT description FROM appointment_type WHERE id = ?", [request.form['treatment']], True)
            email = query_db("select email from users where id = ?", [session['id']], True)
            # Virkar ekki í skólanum (msg):
            msg = Message("Appointment Confirmation - Klillklipp",
                          sender="klippiloka@gmail.com",
                          recipients=[email['email']])
            msg.html = "<h3>Appointment booking</h3><p>You booked an appointment - this is an confirmation email</p><p>You booked an appointment at KlillKlipp, this email is to confirm your booking.</p><h2>Booking info:</h2><p>Hairdresser:     " + hdresser['username'] + ".</p><p>Treatment:     " + tmeant['description'] + ".</p>"
            if request.form['comment']: msg.html += "<h4>Comment: </h4><p>" + request.form['comment'] + "</p>"
            msg.html += "<a href='http://127.0.0.1:5000/confirm/" + str(key) + "'>Click here to confirm!</a>" # HARDCODE!!!
            mail.send(msg)
            # END virkar ekki í skólanum ^
            flash("Appointment booked! Confirmation mail has been sent!")
    hairdressers = query_db("select * from get_hairdressers")
    treatments = query_db("select * from appointment_type")
    return render_template("appointments.html", hairdressers=hairdressers, treatments=treatments, hairerror=hairerror, treaterror=treaterror)

@app.route('/confirm/<int:number>')
def confirmation(number):
    x = query_db("select appointment_id from confirmations where key = ?", [number], True)
    if x:
        state = query_db("select status from appointments where id = ?", [x['appointment_id']], True)
        if state['status'] == 0:
            g.db.execute("UPDATE appointments SET status = 1 WHERE id = ?", (x['appointment_id'] ,))
            g.db.execute("DELETE FROM confirmations WHERE appointment_id = ?", (x['appointment_id'] ,))
            g.db.commit()
            flash('Appointment confirmed!')
            return redirect(url_for('index'))
    return abort(404)

@app.route('/overview/')
def overview():
    if 'id' not in session:
        flash('Please login to view this page.')
        return redirect(url_for('login'))
    userInfo = query_db('select * from get_users_info where id = ?', [session['id']], True)
    hairAppointments = query_db('select * from get_appointments_by_hairdresserID where user = ?', [session['id']]) #Only confirmed appointments
    custAppointments = query_db('select * from get_appointments_by_customerID where user = ?', [session['id']])
    return render_template('overview.html', userInfo = userInfo, hairAppointments = hairAppointments, custAppointments = custAppointments)

@app.route('/overview/admin', methods = ['GET', 'POST']) #Auka, allir registered users byrja sem guest og customer, hér getur admin breytt því
def admin():
    if 'admin' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        g.db.execute("UPDATE users SET status = ?, rank = ? WHERE id = ?", [request.form["statusSelect"], request.form["rankSelect"], request.form["userSelect"]])
        g.db.commit()
        flash('User Updated.')
    usersInfo = query_db('select * from get_users_info')
    ranks = query_db('select * from rank_info')
    workstatus = query_db('select * from status_info')
    return render_template("admin.html", users = usersInfo, ranks = ranks, workstatus = workstatus)


@app.errorhandler(404)
def not_found(e):
    return render_template("404page.html")

if __name__ == '__main__':
    app.run()