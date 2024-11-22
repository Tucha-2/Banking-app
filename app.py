from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = "super_secret_key"

data_file = "data/users.json"

# Ensure data directory and file exist
os.makedirs("data", exist_ok=True)
if not os.path.exists(data_file):
    with open(data_file, "w") as file:
        json.dump({}, file)


# Helper functions
def load_users():
    with open(data_file, "r") as file:
        return json.load(file)


def save_users(users):
    with open(data_file, "w") as file:
        json.dump(users, file)


def generate_account_number():
    return str(len(load_users()) + 1001)


# Routes
@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()
    if username in users and users[username]["password"] == password:
        session["user"] = username
        return redirect(url_for("dashboard"))
    flash("Invalid username or password.", "error")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        phone = request.form["phone"]
        id_number = request.form["id_number"]
        password = request.form["password"]

        users = load_users()
        account_number = generate_account_number()
        users[account_number] = {
            "name": name,
            "surname": surname,
            "phone": phone,
            "id_number": id_number,
            "password": password,
            "balance": 0,
            "transactions": [],
        }
        save_users(users)
        flash(f"Account created successfully! Your account number is {account_number}", "success")
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    users = load_users()
    user = session["user"]
    account_info = users[user]
    return render_template("dashboard.html", account=account_info)


@app.route("/transactions")
def transactions():
    if "user" not in session:
        return redirect(url_for("home"))

    users = load_users()
    user = session["user"]
    transactions = users[user]["transactions"]
    return render_template("transactions.html", transactions=transactions)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/transaction", methods=["POST"])
def transaction():
    if "user" not in session:
        return redirect(url_for("home"))

    users = load_users()
    user = session["user"]
    action = request.form["action"]
    amount = float(request.form["amount"])
    target_account = request.form.get("target_account")

    if action == "deposit":
        users[user]["balance"] += amount
        users[user]["transactions"].append(["Deposit", amount, None])

    elif action == "withdraw":
        if users[user]["balance"] >= amount:
            users[user]["balance"] -= amount
            users[user]["transactions"].append(["Withdraw", amount, None])
        else:
            flash("Insufficient funds for withdrawal.", "error")
            return redirect(url_for("dashboard"))

    elif action == "transfer":
        if target_account in users and users[user]["balance"] >= amount:
            users[user]["balance"] -= amount
            users[user]["transactions"].append(["Transfer", amount, target_account])
            users[target_account]["balance"] += amount
            users[target_account]["transactions"].append(["Received", amount, user])
        else:
            flash("Transfer failed. Check target account or balance.", "error")
            return redirect(url_for("dashboard"))

    save_users(users)
    flash("Transaction successful.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)