from flask import Flask, request, render_template
import auth

app = Flask(__name__, template_folder="../templates")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        try:
            auth.create_account(username, password)
            return "Account created!"

        except auth.UserAlreadyExistsError:
            return "Username already exists!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if auth.login(username, password):
            return "Login successful!"

        return "Invalid username or password!"

    return render_template("login.html")


def start_server():
    app.run(debug=True)