from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for)

from werkzeug.exceptions import abort

from birthdayjo.auth import login_required
from birthdayjo.db import get_db

bp = Blueprint('blog', __name__, url_prefix='/share')

@bp.route('/blog')
def share():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/share.html', posts=posts)

@bp.route('/create', methods=('GET','POST'))
@login_required
def create():
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
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.share'))
            
    return render_template('blog/create.html')