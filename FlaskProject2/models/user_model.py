def check_user(mysql, username, password):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    return user
