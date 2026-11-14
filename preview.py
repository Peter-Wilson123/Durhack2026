import flask

app = flask.Flask(__name__)

@app.route("/login")
def login():
    return flask.render_template("login.html")

app.run("127.0.0.1", 5001)