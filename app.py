from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from ast import literal_eval
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from tinydb import TinyDB, Query

users = TinyDB('users.json')
characters = TinyDB('characters.json')
traits = TinyDB('traits.json')
baseStats = TinyDB('baseStats.json')    # Never update base traits. This is for read only
app = Flask(__name__)

# Config MySQL
# app.config['MYSQL_HOST'] = 'wandrade1.mysql.pythonanywhere-services.com'
# app.config['MYSQL_USER'] = 'wandrade1'
# app.config['MYSQL_PASSWORD'] = 'lmaolmao1'
# app.config['MYSQL_DB'] = 'wandrade1$myflaskapp'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Register Form Class
class RegisterForm(Form):
    email = StringField('Email', [validators.Length(min=4, max=25)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        # password = sha256_crypt.encrypt(str(form.password.data))
        password = form.password.data
        email = form.email.data
        
        users.insert({'username': username, 'password': password, 'email': email})

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

def getFieldData(fieldName, query):
    result = [str(r[fieldName]) for r in query]
    return result

def getIds(query):
    result = [r.eid for r in query]
    return result

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Get user by username
        User = Query()
        result = users.search(User.username == username)
        if result > 0:
            # Get stored hash
            password = getFieldData("password", result)[0]
            # Compare Passwords
            # if sha256_crypt.verify(password_candidate, password):
            if password == password_candidate:
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout    
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))



# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    Characters = Query()
    result = characters.search(Characters.username == session["username"])
    # characters.insert({'name': 'wescules', 'sex': "Male", 'race': 'asian', 'username': 'wescules'})

    names = getFieldData("name", result)
    ids = getIds(result)
    data = zip(names, ids)

    if result > 0:
        return render_template('dashboard.html', data=data)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

# Article Form Class
class ArticleForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=200)])
    sex = StringField('Sex', [validators.Length(min=1, max=200)])
    age = StringField('Age', [validators.Length(min=1, max=200)])
    height = StringField('Height', [validators.Length(min=1, max=200)])
    race = StringField('Race', [validators.Length(min=1, max=200)])
    weight = StringField('Weight', [validators.Length(min=1, max=200)])
    eyeColor = StringField('Eye Color', [validators.Length(min=1, max=200)])
    hairColor = StringField('Hair Color', [validators.Length(min=1, max=200)])
    backgroundInfo = StringField('Background Info', [validators.Length(min=1, max=200)])

# Add Article
@app.route('/add_character/', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        sex = form.sex.data
        age = form.age.data
        height = form.height.data
        race = form.race.data
        weight = form.weight.data
        eyeColor = form.eyeColor.data
        hairColor = form.hairColor.data
        backgroundInfo = form.backgroundInfo.data
        stats = getDocumentById(1, baseStats.all())[0]
        characters.insert({'name': name, 'stats':stats, 'sex': sex, 'race': race, 'username': session['username'], 'age':age, 'height': height,'weight':weight, 'eyeColor':eyeColor, "hairColor":hairColor, "backgroundInfo": backgroundInfo})
        flash('Character Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

def getDocumentById(id, query):
    result = []
    for doc in query:
        if doc.eid is int(id):
            result.append(doc)
            return result

# Edit Character based on Id
@app.route('/edit_character/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_character(id):
    form = ArticleForm(request.form)

    # populate page on GET
    # cant fucking query by id for some goddamn reason...
    result = getDocumentById(id, characters.all())

    form.name.data = getFieldData("name", result)[0]
    form.sex.data = getFieldData("sex", result)[0]
    form.age.data = getFieldData("age", result)[0]
    form.height.data = getFieldData("height", result)[0]
    form.race.data = getFieldData("race", result)[0]
    form.weight.data = getFieldData("weight", result)[0]
    form.eyeColor.data = getFieldData("eyeColor", result)[0]
    form.hairColor.data = getFieldData("hairColor", result)[0]
    form.backgroundInfo.data = getFieldData("backgroundInfo", result)[0]

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        sex = request.form['sex']
        age = request.form['age']
        height = request.form['height']
        race = request.form['race']
        weight = request.form['weight']
        eyeColor = request.form['eyeColor']
        hairColor = request.form['hairColor']
        backgroundInfo = request.form['backgroundInfo']

        # write back to json store because update structs are fucked
        for res in result:
            res['name'] = name
            res['sex'] = sex
            res['age'] = age
            res['height'] = height
            res['weight'] = weight
            res['eyeColor'] = eyeColor
            res['hairColor'] = hairColor
            res['backgroundInfo'] = backgroundInfo
            res['race'] = race
        characters.write_back(result)
        flash('Character Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_character.html', form=form, id=id)

# Add traits to character
# TODO on GET load quantity
@app.route('/add_traits/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def add_traits(id):
    
    # traits.insert({'ap': 3, 'description': 'some description', 'name': 'some name'})
    character = getDocumentById(id, characters.all())[0]

    result = traits.all()
    ap = getFieldData("ap", result)
    description = getFieldData("description", result)
    name = getFieldData("name", result)
    effect = getFieldData('effect', result)

    columns = zip(ap, description, name, effect)
    if request.method == 'POST':
        quantity = request.form['text']
        effects = literal_eval(request.form['effect'])      # turn unicode to dict

        # update the character based on quantity of trait allocated
        for key in effects:
            character['stats'][key] = quantity * effects[key]
        characters.write_back([character])

        flash('Added Traits', 'success')
        flash(character, 'success')

    return render_template('traits.html', columns=columns, id=id)

@app.route('/character_sheet/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def character_sheet(id):
    
    # traits.insert({'ap': 3, 'description': 'some description', 'name': 'some name'})
    character = getDocumentById(id, characters.all())[0]

    result = traits.all()
    ap = getFieldData("ap", result)
    description = getFieldData("description", result)
    name = getFieldData("name", result)
    effect = getFieldData('effect', result)

    columns = zip(ap, description, name, effect)
    if request.method == 'POST':
        quantity = request.form['text']
        effects = literal_eval(request.form['effect'])      # turn unicode to dict

        # update the character based on quantity of trait allocated
        for key in effects:
            character['stats'][key] = quantity * effects[key]
        characters.write_back([character])

        flash('Added Traits', 'success')
        flash(character, 'success')

    return render_template('character.html', columns=columns, id=id)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
    
#sudo apt-get install mysql-server
#apt-get install python-dev
#sudo apt-get install libmysqlclient-dev
#pip install flask_mysqldb
#pip install wtforms
#pip install passlib

###################
#***create database***(set password to 'root')
# mysql -u root -p
# create database myflaskapp;
# mysql -u root -proot myflaskapp < admin_backup.sql
