from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .database import (create_session, get_session, get_sessions_by_user,
    save_target_allocations, get_target_allocations,
    add_stock, get_stocks, delete_stock,
    save_analysis_results, get_analysis_results,
    create_user, get_user_by_email, get_user_by_id)
from .analysis import run_analysis
from .stock_price import get_live_price

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

@main.route("/new-session")
@login_required
def new_session():
    user_id  = session["user_id"]
    username = session.get("username", "User")
    sid = create_session(dbu(), dbt(), user_id=user_id, label=username)
    session["session_id"] = sid
    return redirect(url_for("main.target_allocation", session_id=sid))

@main.route("/session/<int:session_id>/targets", methods=["GET", "POST"])
@login_required
def target_allocation(session_id):
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

@main.route("/api/get-price")
@login_required
def api_get_price():
    """
    API endpoint called by JavaScript when user types a stock name.
    Returns live price as JSON.
    """
    stock_name = request.args.get("stock", "").strip()
    if not stock_name:
        return jsonify({"success": False, "error": "No stock name provided"})
    result = get_live_price(stock_name)
    return jsonify(result)

@main.route("/session/<int:session_id>/stocks", methods=["GET", "POST"])
@login_required
def add_stocks(session_id):
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
            flash(f"'{name}' added successfully!", "success")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    stocks = get_stocks(dbu(), dbt(), session_id)
    return render_template("add_stocks.html", session_id=session_id,
                           sectors=sectors, stocks=stocks)

@main.route("/session/<int:session_id>/stocks/<int:stock_id>/delete", methods=["POST"])
@login_required
def remove_stock(session_id, stock_id):
    delete_stock(dbu(), dbt(), stock_id)
    flash("Stock removed.", "warning")
    return redirect(url_for("main.add_stocks", session_id=session_id))

@main.route("/session/<int:session_id>/analyze")
@login_required
def analyze(session_id):
    stocks  = get_stocks(dbu(), dbt(), session_id)
    targets = get_target_allocations(dbu(), dbt(), session_id)
    if not stocks:
        flash("Please add at least one stock before analyzing.", "danger")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    results = run_analysis(stocks, targets)
    save_analysis_results(dbu(), dbt(), session_id, results)
    return redirect(url_for("main.results", session_id=session_id))

@main.route("/session/<int:session_id>/results")
@login_required
def results(session_id):
    analysis = get_analysis_results(dbu(), dbt(), session_id)
    stocks   = get_stocks(dbu(), dbt(), session_id)
    sess     = get_session(dbu(), dbt(), session_id)
    if not analysis:
        flash("No results found. Please run the analysis first.", "danger")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    total_value = sum(
        float(s["quantity"]) * float(s["buy_price"]) for s in stocks if s["buy_price"]
    )
    for row in analysis:
        row["actual_value"] = round((row["actual_pct"] / 100) * total_value, 2)
        row["target_value"] = round((row["target_pct"] / 100) * total_value, 2)
        row["gap_value"]    = round(row["actual_value"] - row["target_value"], 2)
        if row["status"] == "overweight":
            row["action"]        = "Reduce"
            row["action_amount"] = abs(row["gap_value"])
        elif row["status"] == "underweight":
            row["action"]        = "Increase"
            row["action_amount"] = abs(row["gap_value"])
        else:
            row["action"]        = "Hold"
            row["action_amount"] = 0

    # Smart rebalancing — fetch live prices for each stock
    # and calculate how many shares to buy/sell
    rebalancing = []
    for row in analysis:
        if row["action"] == "Hold":
            continue
        sector_stocks = [s for s in stocks if s["sector"] == row["sector"]]
        suggestions   = []
        for stock in sector_stocks:
            live = get_live_price(stock["name"])
            if live["success"] and live["price"] > 0:
                current_price = live["price"]
            else:
                current_price = float(stock["buy_price"])
            if current_price > 0:
                shares = abs(row["gap_value"]) / current_price
                suggestions.append({
                    "stock":         stock["name"],
                    "action":        row["action"],
                    "current_price": current_price,
                    "shares":        round(shares, 2),
                    "amount":        abs(row["gap_value"]),
                })
        if suggestions:
            rebalancing.append({
                "sector":      row["sector"],
                "action":      row["action"],
                "suggestions": suggestions,
            })

    return render_template("results.html",
                           session_id=session_id,
                           analysis=analysis,
                           stocks=stocks,
                           sess=sess,
                           total_value=total_value,
                           rebalancing=rebalancing)

@main.route("/history")
@login_required
def history():
    sessions = get_sessions_by_user(dbu(), dbt(), session["user_id"])
    return render_template("history.html", sessions=sessions)
