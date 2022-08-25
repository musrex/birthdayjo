from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, send_from_directory, current_app)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from birthdayjo.auth import login_required
from birthdayjo.db import get_db
import uuid

import os
import imghdr
bp = Blueprint('blog', __name__, url_prefix='/')

def validate_image(stream):
    header = stream.read(512) # 512 bytes should be enough for a header check
    stream.seek(0) # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@bp.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@bp.route('/create/')
def index():
    files = os.listdir(current_app.config['UPLOAD_PATH'])
    return render_template('/blog/create.html', files=files)

@bp.route('/create/', methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None   
        if os.path.exists(g.user['username']) is False:
            os.makedirs(g.user['username'])
        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            for uploaded_file in request.files.getlist('file'):
                filename = secure_filename(uploaded_file.filename)    
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                            file_ext != validate_image(uploaded_file.stream):
                        return "Invalid image", 400
                    filename = uuid.uuid4().hex
                    uploaded_file.save(os.path.join(g.user['username'], filename + file_ext))
                    return redirect(url_for('blog.gallery'))
    
@bp.route('/static/img/<filename>')
def upload(filename):
    return send_from_directory(current_app.config['UPLOAD_PATH'], filename)

@bp.route('/blog')
def gallery():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/gallery.html', posts=posts)

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