from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    db = current_app.config['db']
    users_collection = db['users']

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            return "User already exists"

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({'username': username, 'password': hashed_password})
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    db = current_app.config['db']
    users_collection = db['users']

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))

        return "Invalid username or password"

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth.login'))


@auth_bp.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    db = current_app.config['db']
    users_collection = db['users']

    user = users_collection.find_one({'username': session['username']})

    if request.method == 'POST':
        new_username = request.form.get('username')
        email = request.form.get('email')

        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {
                'username': new_username,
                'email': email
            }}
        )

        # update session in case username changed
        session['username'] = new_username

        return redirect(url_for('index'))

    return render_template('edit_account.html', user=user)