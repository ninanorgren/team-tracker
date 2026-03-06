from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
import requests

from app.auth.forms import LoginForm, RegistrationForm
from app.extensions import db, limiter
from app.models import User


auth_bp = Blueprint("auth", __name__)


def verify_recaptcha():
    if not current_app.config["RECAPTCHA_ENABLED"]:
        return True

    token = request.form.get("g-recaptcha-response", "").strip()
    if not token:
        flash("Please complete the reCAPTCHA challenge.", "danger")
        return False

    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": current_app.config["RECAPTCHA_SECRET_KEY"],
        "response": token,
        "remoteip": request.remote_addr,
    }

    try:
        response = requests.post(verify_url, data=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        current_app.logger.warning("reCAPTCHA verification failed: %s", exc)
        flash(
            "Could not verify reCAPTCHA right now. Please try again.",
            "warning",
        )
        return False

    if not response.json().get("success", False):
        flash("reCAPTCHA validation failed. Please try again.", "danger")
        return False

    return True


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("8 per minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        if not verify_recaptcha():
            return render_template(
                "auth/register.html",
                form=form,
                recaptcha_site_key=current_app.config["RECAPTCHA_SITE_KEY"],
            )

        user = User(
            display_name=form.display_name.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Your account has been created.", "success")
        return redirect(url_for("main.index"))

    return render_template(
        "auth/register.html",
        form=form,
        recaptcha_site_key=current_app.config["RECAPTCHA_SITE_KEY"],
    )


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=False)

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)

            flash("You are now logged in.", "success")
            return redirect(url_for("main.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
