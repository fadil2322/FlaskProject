from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        mysql = current_app.config['mysql']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, theme FROM user WHERE username=%s AND password=%s", (username, pw))
        user = cur.fetchone()
        cur.close()
        if user:
            session['username'] = username
            session['theme'] = user[1]
            flash('Login berhasil', 'success')
            return redirect(url_for('auth.login'))  # biarkan kembali ke login, js akan redirect ke dashboard
        else:
            flash('Username atau Password salah.', 'error')
            return redirect(url_for('auth.login'))
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
