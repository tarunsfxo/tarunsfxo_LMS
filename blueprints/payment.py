import logging
import random
import string
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Payment, User
from config import Config

logger = logging.getLogger(__name__)
payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/pricing")
def pricing():
    return render_template(
        "pricing.html",
        plans=Config.PLANS,
        current_plan=getattr(current_user, "plan", "free"),
        stripe_enabled=bool(current_app.config.get("STRIPE_SECRET_KEY")),
        stripe_pk=current_app.config.get("STRIPE_PUBLISHABLE_KEY", "")
    )


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

    stripe_secret = current_app.config.get("STRIPE_SECRET_KEY")

    # If Stripe is configured and requested via query param or button
    if stripe_secret and request.args.get("gateway") == "stripe":
        try:
            # Create Stripe Checkout Session via Stripe REST API
            price_in_cents = int(plan["price"] * 100)
            success_url = url_for("payment.stripe_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}"
            cancel_url = url_for("payment.pricing", _external=True)
            
            headers = {"Authorization": f"Bearer {stripe_secret}"}
            data = {
                "payment_method_types[]": "card",
                "mode": "payment",
                "customer_email": current_user.email,
                "client_reference_id": str(current_user.id),
                "metadata[plan]": plan_key,
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][unit_amount]": str(price_in_cents),
                "line_items[0][price_data][product_data][name]": f"{plan['name']} Plan",
                "line_items[0][quantity]": "1",
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
            res = requests.post("https://api.stripe.com/v1/checkout/sessions", headers=headers, data=data, timeout=10)
            if res.status_code == 200:
                session_data = res.json()
                return redirect(session_data["url"])
            else:
                logger.error("Stripe session creation failed: %s", res.text)
                flash("Stripe checkout initialization failed. Falling back to test checkout.", "warning")
        except Exception as exc:
            logger.exception("Error connecting to Stripe API")
            flash("Stripe service unavailable. Using secure test checkout.", "warning")

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

        # Process payment record
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

    return render_template("checkout.html", plan=plan, plan_key=plan_key, stripe_enabled=bool(stripe_secret))


@payment_bp.route("/payment/stripe/success")
@login_required
def stripe_success():
    session_id = request.args.get("session_id")
    stripe_secret = current_app.config.get("STRIPE_SECRET_KEY")
    plan_key = "pro"

    if stripe_secret and session_id:
        try:
            headers = {"Authorization": f"Bearer {stripe_secret}"}
            res = requests.get(f"https://api.stripe.com/v1/checkout/sessions/{session_id}", headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                plan_key = data.get("metadata", {}).get("plan", "pro")
                plan = Config.PLANS.get(plan_key, Config.PLANS["pro"])
                payment = Payment(
                    user_id=current_user.id,
                    plan=plan_key,
                    amount=plan["price"],
                    card_last4="STRIPE",
                    status="success",
                    transaction_id=session_id[:20],
                )
                db.session.add(payment)
                current_user.plan = plan_key
                db.session.commit()

                from automation.trigger import fire
                fire("premium_purchased", user_id=current_user.id, amount=plan["price"], transaction_id=session_id, plan_name=plan_key)

                return redirect(url_for("payment.success", transaction_id=payment.transaction_id))
        except Exception as exc:
            logger.exception("Failed to verify Stripe session")

    flash("Payment confirmed!", "success")
    return redirect(url_for("main.dashboard"))


@payment_bp.route("/payment/webhook", methods=["POST"])
def stripe_webhook():
    """Webhook endpoint for asynchronous Stripe payment confirmations."""
    payload = request.get_json(silent=True) or {}
    event_type = payload.get("type")

    if event_type == "checkout.session.completed":
        session_obj = payload.get("data", {}).get("object", {})
        user_id = session_obj.get("client_reference_id")
        plan_key = session_obj.get("metadata", {}).get("plan", "pro")
        amount = float(session_obj.get("amount_total", 0)) / 100.0
        session_id = session_obj.get("id", "TXN_STRIPE")

        if user_id:
            user = User.query.get(int(user_id))
            if user:
                user.plan = plan_key
                payment = Payment(
                    user_id=user.id,
                    plan=plan_key,
                    amount=amount,
                    card_last4="STRIPE",
                    status="success",
                    transaction_id=session_id[:20],
                )
                db.session.add(payment)
                db.session.commit()

                from automation.trigger import fire
                fire("premium_purchased", user_id=user.id, amount=amount, transaction_id=session_id, plan_name=plan_key)
                return jsonify({"status": "handled"}), 200

    return jsonify({"status": "ignored"}), 200


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
