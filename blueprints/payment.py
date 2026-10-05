import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Payment
from config import Config

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/pricing")
def pricing():
    return render_template("pricing.html", plans=Config.PLANS, current_plan=getattr(current_user, "plan", "free"))


@payment_bp.route("/checkout/<plan_key>", methods=["GET", "POST"])
@login_required
def checkout(plan_key):
    if plan_key not in Config.PLANS:
        flash("Invalid plan selected.", "danger")
        return redirect(url_for("payment.pricing"))

    plan = Config.PLANS[plan_key]

    if plan_key == "free":
        current_user.plan = "free"
        db.session.commit()
        flash("You're now on the Free plan.", "info")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        card_number = request.form.get("card_number", "").replace(" ", "")
        card_name = request.form.get("card_name", "").strip()
        expiry = request.form.get("expiry", "")
        cvv = request.form.get("cvv", "")

        errors = []
        if len(card_number) != 16 or not card_number.isdigit():
            errors.append("Card number must be 16 digits.")
        if not card_name:
            errors.append("Cardholder name is required.")
        if len(cvv) not in (3, 4) or not cvv.isdigit():
            errors.append("Invalid CVV.")
        if "/" not in expiry:
            errors.append("Expiry must be in MM/YY format.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("checkout.html", plan=plan, plan_key=plan_key)

        # Simulate fake transaction processing
        transaction_id = "TXN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
        payment = Payment(
            user_id=current_user.id,
            plan=plan_key,
            amount=plan["price"],
            card_last4=card_number[-4:],
            status="success",
            transaction_id=transaction_id,
        )
        db.session.add(payment)
        current_user.plan = plan_key
        db.session.commit()
        
        from automation.trigger import fire
        fire("premium_purchased", user_id=current_user.id, amount=plan["price"], transaction_id=transaction_id, plan_name=plan_key)

        return redirect(url_for("payment.success", transaction_id=transaction_id))

    return render_template("checkout.html", plan=plan, plan_key=plan_key)


@payment_bp.route("/payment/success/<transaction_id>")
@login_required
def success(transaction_id):
    payment = Payment.query.filter_by(transaction_id=transaction_id, user_id=current_user.id).first_or_404()
    return render_template("payment_success.html", payment=payment)


@payment_bp.route("/billing/history")
@login_required
def history():
    payments = current_user.payments.order_by(Payment.created_at.desc()).all()
    return render_template("billing_history.html", payments=payments)
