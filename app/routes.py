from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from .database import (create_session, get_session, get_sessions_by_user,
    save_target_allocations, get_target_allocations,
    add_stock, get_stocks, delete_stock,
    save_analysis_results, get_analysis_results,
    create_user, get_user_by_email, get_user_by_id)
from .analysis import run_analysis
import csv
import io

main = Blueprint("main", __name__)

def dbu():
    return current_app.config["DATABASE_URL"]

def dbt():
    return current_app.config["DB_TYPE"]

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/about")
def about():
    return render_template("about.html")

@main.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("main.index"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("signup.html")
        existing = get_user_by_email(dbu(), dbt(), email)
        if existing:
            flash("An account with this email already exists. Please log in.", "danger")
            return render_template("signup.html")
        password_hash = generate_password_hash(password)
        user_id = create_user(dbu(), dbt(), name, email, password_hash)
        session["user_id"]  = user_id
        session["username"] = name
        flash(f"Welcome, {name}! Your account has been created.", "success")
        return redirect(url_for("main.index"))
    return render_template("signup.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.index"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(dbu(), dbt(), email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("login.html")
        session["user_id"]  = user["id"]
        session["username"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("main.index"))
    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))

@main.route("/guest-session")
def guest_session():
    """
    Creates a temporary guest session — no account needed.
    Guest sessions are not saved to any user account.
    The data disappears when the browser session ends.
    """
    sid = create_session(dbu(), dbt(), user_id=None, label="Guest")
    session["session_id"] = sid
    session["username"]   = "Guest"
    session["is_guest"]   = True
    return redirect(url_for("main.target_allocation", session_id=sid))

@main.route("/new-session")
@login_required
def new_session():
    user_id  = session["user_id"]
    username = session.get("username", "User")
    sid = create_session(dbu(), dbt(), user_id=user_id, label=username)
    session["session_id"] = sid
    return redirect(url_for("main.target_allocation", session_id=sid))

@main.route("/session/<int:session_id>/targets", methods=["GET", "POST"])
def target_allocation(session_id):
    if not session.get("user_id") and not session.get("is_guest"):
        flash("Please log in to continue.", "warning")
        return redirect(url_for("main.login"))
    existing = get_target_allocations(dbu(), dbt(), session_id)
    if request.method == "POST":
        sectors = request.form.getlist("sector")
        percentages = request.form.getlist("pct")
        allocations = []
        total = 0.0
        error = None
        for sector, pct in zip(sectors, percentages):
            sector = sector.strip()
            if not sector:
                continue
            try:
                pct_val = float(pct)
            except ValueError:
                error = f"'{pct}' is not a valid number."
                break
            if pct_val <= 0:
                error = "All percentages must be greater than 0."
                break
            total += pct_val
            allocations.append({"sector": sector, "target_pct": pct_val})
        if not error and len(allocations) == 0:
            error = "Please add at least one sector."
        if not error and round(total, 2) != 100.0:
            error = f"Your percentages add up to {total:.1f}%. They must total exactly 100%."
        if error:
            flash(error, "danger")
            return render_template("target_allocation.html", session_id=session_id, existing=existing)
        save_target_allocations(dbu(), dbt(), session_id, allocations)
        flash("Target allocations saved!", "success")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    return render_template("target_allocation.html", session_id=session_id, existing=existing)

@main.route("/session/<int:session_id>/stocks", methods=["GET", "POST"])
def add_stocks(session_id):
    if not session.get("user_id") and not session.get("is_guest"):
        flash("Please log in to continue.", "warning")
        return redirect(url_for("main.login"))
    targets = get_target_allocations(dbu(), dbt(), session_id)
    sectors = [t["sector"] for t in targets]
    if request.method == "POST":
        name      = request.form.get("name", "").strip()
        quantity  = request.form.get("quantity", "").strip()
        buy_price = request.form.get("buy_price", "").strip()
        sector    = request.form.get("sector", "").strip()
        error = None
        if not name:
            error = "Please enter the stock name."
        elif not quantity:
            error = "Please enter the quantity."
        elif not buy_price:
            error = "Please enter the buy price."
        elif not sector:
            error = "Please select a sector."
        else:
            try:
                qty_val   = float(quantity)
                price_val = float(buy_price)
                if qty_val <= 0:
                    error = "Quantity must be greater than 0."
                elif price_val <= 0:
                    error = "Buy price must be greater than 0."
            except ValueError:
                error = "Quantity and price must be numbers."
        if error:
            flash(error, "danger")
        else:
            add_stock(dbu(), dbt(), session_id,
                      name=name, quantity=float(quantity),
                      buy_price=float(buy_price), sector=sector)
            flash(f"'{
