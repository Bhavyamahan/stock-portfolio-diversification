from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from .database import (create_session, get_session, get_all_sessions,
    save_target_allocations, get_target_allocations,
    add_stock, get_stocks, delete_stock,
    save_analysis_results, get_analysis_results)
from .analysis import run_analysis

main = Blueprint("main", __name__)

def db():
    return current_app.config["DATABASE"]

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/new-session")
def new_session():
    username = request.args.get("username", "User").strip() or "User"
    sid = create_session(db(), label=username)
    session["session_id"] = sid
    session["username"]   = username
    return redirect(url_for("main.target_allocation", session_id=sid))

@main.route("/session/<int:session_id>/targets", methods=["GET", "POST"])
def target_allocation(session_id):
    existing = get_target_allocations(db(), session_id)
    if request.method == "POST":
        sectors     = request.form.getlist("sector")
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
        save_target_allocations(db(), session_id, allocations)
        flash("Target allocations saved!", "success")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    return render_template("target_allocation.html", session_id=session_id, existing=existing)

@main.route("/session/<int:session_id>/stocks", methods=["GET", "POST"])
def add_stocks(session_id):
    targets = get_target_allocations(db(), session_id)
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
            add_stock(db(), session_id, name=name,
                      quantity=float(quantity),
                      buy_price=float(buy_price),
                      sector=sector)
            flash(f"'{name}' added successfully!", "success")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    stocks = get_stocks(db(), session_id)
    return render_template("add_stocks.html", session_id=session_id,
                           sectors=sectors, stocks=stocks)

@main.route("/session/<int:session_id>/stocks/<int:stock_id>/delete", methods=["POST"])
def remove_stock(session_id, stock_id):
    delete_stock(db(), stock_id)
    flash("Stock removed.", "warning")
    return redirect(url_for("main.add_stocks", session_id=session_id))

@main.route("/session/<int:session_id>/analyze")
def analyze(session_id):
    stocks  = get_stocks(db(), session_id)
    targets = get_target_allocations(db(), session_id)
    if not stocks:
        flash("Please add at least one stock before analyzing.", "danger")
        return redirect(url_for("main.add_stocks", session_id=session_id))
    results, total_value = run_analysis(stocks, targets)
    save_analysis_results(db(), session_id, results)
    return redirect(url_for("main.results", session_id=session_id))

@main.route("/session/<int:session_id>/results")
def results(session_id):
    analysis    = get_analysis_results(db(), session_id)
    stocks      = get_stocks(db(), session_id)
    sess        = get_session(db(), session_id)
    if not analysis:
        flash("No results found. Please run the analysis first.", "danger")
        return redirect(url_for("main.add_stocks", session_id=session_id))

    # Calculate total portfolio value for rebalancing table
    total_value = sum(s["quantity"] * s.get("buy_price", 1) for s in stocks)

    return render_template("results.html",
                           session_id=session_id,
                           analysis=analysis,
                           stocks=stocks,
                           sess=sess,
                           total_value=total_value)

@main.route("/history")
def history():
    sessions = get_all_sessions(db())
    return render_template("history.html", sessions=sessions)
