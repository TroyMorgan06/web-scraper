#!/usr/bin/env python3
"""Small Flask UI for the Universal Product Tracker."""

from flask import Flask, flash, redirect, render_template, request, url_for

from app.config import FLASK_SECRET_KEY
from app.db import get_history, get_product_by_id, init_db, list_products
from app.tracker import check_product

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


@app.before_request
def ensure_db():
    init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = (request.form.get("url") or "").strip()
        if not url:
            flash("Please enter a product URL.", "error")
            return redirect(url_for("index"))
        try:
            result = check_product(url, send_alerts=True)
            product = result["product"]
            msg = f"Tracked: {product['title'] or url} — ${product['last_price']}"
            if result["price_changed"]:
                msg += " (price changed"
                msg += "; email sent)" if result["alert_sent"] else "; email not sent)"
            flash(msg, "success")
        except Exception as exc:
            flash(f"Failed to scrape URL: {exc}", "error")
        return redirect(url_for("index"))

    products = list_products()
    return render_template("index.html", products=products)


@app.route("/history")
@app.route("/history/<int:product_id>")
def history(product_id=None):
    product = get_product_by_id(product_id) if product_id is not None else None
    if product_id is not None and product is None:
        flash(f"No product with id {product_id}", "error")
        return redirect(url_for("index"))
    rows = get_history(product_id)
    return render_template(
        "history.html",
        rows=rows,
        product=product,
        product_id=product_id,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)