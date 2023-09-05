import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///inventory.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, quantity INTEGER);
# CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL);
# CREATE TABLE items_tags (item_id INTEGER, tag_id INTEGER, FOREIGN KEY (item_id) REFERENCES items(id), FOREIGN KEY (tag_id) REFERENCES tags(id));

# CREATE TABLE locations (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name NOT NULL);
# CREATE TABLE items_locations (item_id INTEGER, location_id INTEGER, FOREIGN KEY (item_id) REFERENCES items(id), FOREIGN KEY (location_id) REFERENCES locations(id));





@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""


    session.clear()

    if request.method == "POST":
        username = request.form.get("username")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) > 0 or len(username) == 0:
            return apology("invalid username")

        password = request.form.get("password")
        if len(password) == 0 or password != request.form.get("confirmation"):
            return apology("invalid password")

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        return render_template("index.html")

    else:
        return render_template("register.html")


@app.route("/")
def index():
    """Show all Items"""

    items = db.execute("SELECT name, quantity FROM items;")
    data = []
    for item in items:
        data.append([item["name"], item["quantity"]])

    return render_template("index.html", keys=["Item", "Quantity"], data=data)

@app.route("/items", methods=["GET", "POST"])
@login_required
def items():
    print(request.method)
    if request.method == "GET":
        items = db.execute("SELECT name, quantity FROM items;")

        return render_template("items.html", items=items)

    if request.method == "POST":
        name = request.form.get("name")
        if name != None: # add item
            quantity = int(request.form.get("quantity"))

            db.execute("INSERT INTO items (name, quantity) VALUES (?,?)", name, quantity)

            return redirect("/items")

        id = db.execute("SELECT id FROM items WHERE name=?", request.form.get("value"))[0]["id"]

        return redirect("/item?id=" + str(id))


    return apology("TODO")

@app.route("/item", methods=["GET", "POST"])
@login_required
def item():
    if request.method == "GET":
        id = request.args.get("id")
        item = db.execute("SELECT name, id, quantity FROM items WHERE id=?", id)
        if len(item) != 1:
            return apology("Non-Existant Item")

        # {'name': 'Test', 'id': 2, 'quantity': 'AA'}

        tags = db.execute("SELECT name FROM tags WHERE id IN (SELECT tag_id FROM items_tags WHERE item_id=?)", id)
        #tags.append({"name": "tag"})
        not_tags = db.execute("SELECT name FROM tags WHERE id NOT IN (SELECT tag_id FROM items_tags WHERE item_id=?)", id)

        return render_template("item.html", item=item[0], id=item[0]["id"], tags=tags, not_tags=not_tags)

    if request.method == "POST":
        match request.args.get("a"):
            case "d":
                if request.form.get("confirm"):
                    db.execute("DELETE FROM items WHERE id=?", request.args.get("id"))
                    return redirect("/items")
                return redirect("/item?id=" + request.args.get("id"))
            case "a":
                tag = request.form.get("value")
                print(tag)
                tag_id = db.execute("SELECT id FROM tags WHERE name=?", tag)[0]["id"]
                db.execute("INSERT INTO items_tags (item_id, tag_id) VALUES (?,?)", request.args.get("id"), tag_id)
                return redirect("/item?id=" + request.args.get("id"))
            case "s":
                tag = request.form.get("value")
                tag_id = db.execute("SELECT id FROM tags WHERE name=?", tag)[0]["id"]
                db.execute("DELETE FROM items_tags WHERE item_id=? AND tag_id=?", request.args.get("id"), tag_id)
                return redirect("/item?id=" + request.args.get("id"))
            case "r":
                name = request.form.get("name")
                if name != "":
                    db.execute("UPDATE items SET name=? WHERE id=?", name, request.args.get("id"))
                return redirect("/item?id=" + request.args.get("id"))
            case _:
                return redirect("/item?id=" + request.args.get("id"))
        return apology("TODO")
    return apology("TODO")


@app.route("/tags", methods=["GET", "POST"])
@login_required
def tags():
    if request.method == "GET":
        tags = db.execute("SELECT name FROM tags")
        return render_template("tags.html", tags=tags)

    if request.method == "POST":
        name = request.form.get("name")
        if name != None: # add tag
            db.execute("INSERT INTO tags (name) VALUES (?)", name)
            return redirect("/tags")

        id = db.execute("SELECT id FROM tags WHERE name=?", request.form.get("value"))[0]["id"]
        return redirect("/tag?id=" + str(id))


    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    return apology("TODO")

@app.route("/history")
@login_required
def history():
    return apology("TODO")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    return apology("TODO")




@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    return apology("TODO")
