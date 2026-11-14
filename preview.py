import flask

app = flask.Flask(__name__)

# base.html checks current_user; pretend nobody is signed in
@app.context_processor
def fake_user():
    class Anonymous:
        is_authenticated = False
    return {"current_user": Anonymous()}

# The home page needs the database and APIs: run app.py to see it
@app.route("/login")
def login():
    return flask.render_template("login.html")

@app.route("/register")
def register():
    return flask.render_template("register.html")

app.run("127.0.0.1", 5001)