#!venv/bin/python
from flask import redirect, url_for, render_template, flash, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_user, logout_user, current_user, login_required
from oauth import OAuthSignIn
from models import User
from hackru import app, lm, db
from werkzeug import secure_filename
import os


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dash():
    if request.method == 'GET':
        return render_template('dashboard.html',
                                name=current_user.name)


@app.route('/confirm', methods=['GET'])
@login_required
def confirm():
    if request.method == 'GET':
        current_user.confirmed = True
        db.session.commit()
        return render_template('confirm.html')


@app.route('/stats/<provider>', methods=['GET'])
@login_required
def stats(provider):
    if current_user.is_admin:
        oauth = OAuthSignIn.get_provider(provider)
        users = oauth.get_users()
        return render_template('stats.html', users=users)
    else:
        return redirect(url_for('index'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'GET':
        github = current_user.github
        comments = current_user.comments
        if github is None: github = ""
        if comments is None: comments = ""
        return render_template('account.html',
                                github=github,
                                comments=comments)
    if request.method == 'POST':
        github = request.form.get('github')
        comments = request.form.get('comments')

        if github is None:
            github = ""
        else:
            current_user.github = github
            db.session.commit()

        if comments is None:
            comments = ""
        else:
            current_user.comments = comments
            db.session.commit()

        # Upload file handling
        file = request.files['resume']
        if file:
            if allowed_file(file.filename):
                filename = str(current_user.mlh_id) + "_" + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.resume = filename
                db.session.commit()
                # Delete old resume
                path = os.path.abspath(app.config['UPLOAD_FOLDER'])
                list = os.listdir(path)
                for item in list:
                    id = int(item.split('_')[0])
                    if id == current_user.mlh_id and filename != item:
                        os.remove(os.path.join(path, item))

                flash("Successfully updated information!")
            else:
                flash("Invalid file type! Please upload a PDF, TXT, DOC, DOCX")

        return render_template('account.html',
                                github=github,
                                comments=comments,
                                filename=file.filename)


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    mlh_id, name, email = oauth.callback()
    if mlh_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(mlh_id=mlh_id).first()
    if not user:
        user = User(mlh_id=mlh_id, name=name, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
