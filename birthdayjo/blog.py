from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory)

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from birthdayjo.auth import login_required
from birthdayjo.db import get_db

import os

bp = Blueprint('blog', __name__, url_prefix='/gallery')

def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# @bp.route('/create/', methods=['GET','POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if post request has the file part
#         if 'file' not in request.files:
#             flash('Error 1: No file selected.')
#             return redirect(url_for('blog.create'))
#         file = request.files['upload']
#         # if the user does not select a file, the browser submits an
#         # empty file without a filename
#         if file.filename == '':
#             flash('Error 2: No file selected.')
#             return redirect('blog.create')
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('download_file', name=filename))
#     return redirect(url_for('blog.gallery'))


@bp.route('/static/img/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@bp.route('/blog')
def gallery():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, filename'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/gallery.html', posts=posts)

@bp.route('/create/', methods=('GET','POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        file = request.files['upload']
        error = None
        
        if not title:
            error = 'Title is required.'
       
        #if 'file' not in request.files:
         #   error = 'Error 1: No file selected.'

        if file.filename == '':
             flash('Error 2: No file selected.')

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, filename)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], file)
            )
            db.commit()
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('blog.gallery'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body =?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.gallery'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.gallery'))