import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Certificate, Category, Progress, Bite
from certificates import generate_certificate_code, generate_certificate_pdf

certificate_bp = Blueprint("certificate", __name__)

@certificate_bp.route("/certificates")
@login_required
def list_certificates():
    certs = current_user.certificates.order_by(Certificate.issued_at.desc()).all()
    categories = Category.query.all()

    eligible = []
    for cat in categories:
        total_in_cat = Bite.query.filter_by(category_id=cat.id).count()
        completed_in_cat = (
            Progress.query.join(Bite, Progress.bite_id == Bite.id)
            .filter(Progress.user_id == current_user.id, Progress.completed == True, Bite.category_id == cat.id)
            .count()
        )
        already_issued = Certificate.query.filter_by(user_id=current_user.id, category_id=cat.id).first()
        if total_in_cat > 0 and completed_in_cat == total_in_cat and not already_issued:
            eligible.append((cat, completed_in_cat))

    return render_template("certificates.html", certs=certs, eligible=eligible)


@certificate_bp.route("/certificates/generate/<int:category_id>", methods=["POST"])
@login_required
def generate(category_id):
    category = Category.query.get_or_404(category_id)

    completed_in_cat = (
        Progress.query.join(Bite, Progress.bite_id == Bite.id)
        .filter(Progress.user_id == current_user.id, Progress.completed == True, Bite.category_id == category.id)
        .count()
    )

    total_in_cat = Bite.query.filter_by(category_id=category.id).count()

    if total_in_cat == 0 or completed_in_cat < total_in_cat:
        flash(f"Complete all bites in {category.name} to earn this certificate.", "warning")
        return redirect(url_for("certificate.list_certificates"))

    existing = Certificate.query.filter_by(user_id=current_user.id, category_id=category.id).first()
    if existing:
        flash("Certificate already issued for this category.", "info")
        return redirect(url_for("certificate.list_certificates"))

    cert_code = generate_certificate_code()
    filepath, filename = generate_certificate_pdf(
        current_app.config["CERTIFICATES_FOLDER"],
        current_user.username,
        category.name,
        cert_code,
        completed_in_cat,
    )

    cert = Certificate(
        user_id=current_user.id,
        category_id=category.id,
        cert_code=cert_code,
        file_path=filename,
    )
    db.session.add(cert)
    current_user.xp += 25
    db.session.commit()

    flash(f"🎉 Certificate generated for {category.name}!", "success")
    return redirect(url_for("certificate.list_certificates"))


@certificate_bp.route("/certificates/download/<int:cert_id>")
@login_required
def download(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    if cert.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access to certificate.", "danger")
        return redirect(url_for("certificate.list_certificates"))
    
    filepath = os.path.join(current_app.config["CERTIFICATES_FOLDER"], cert.file_path)
    if not os.path.exists(filepath):
        completed_in_cat = Progress.query.join(Bite, Progress.bite_id == Bite.id).filter(
            Progress.user_id == cert.user_id,
            Progress.completed == True,
            Bite.category_id == cert.category_id
        ).count()
        generate_certificate_pdf(
            current_app.config["CERTIFICATES_FOLDER"],
            cert.user.username,
            cert.category.name,
            cert.cert_code,
            completed_in_cat,
        )

    return send_from_directory(
        current_app.config["CERTIFICATES_FOLDER"], cert.file_path, as_attachment=True
    )


@certificate_bp.route("/certificates/view/<int:cert_id>")
@login_required
def view(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    if cert.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access to certificate.", "danger")
        return redirect(url_for("certificate.list_certificates"))
    
    filepath = os.path.join(current_app.config["CERTIFICATES_FOLDER"], cert.file_path)
    if not os.path.exists(filepath):
        completed_in_cat = Progress.query.join(Bite, Progress.bite_id == Bite.id).filter(
            Progress.user_id == cert.user_id,
            Progress.completed == True,
            Bite.category_id == cert.category_id
        ).count()
        generate_certificate_pdf(
            current_app.config["CERTIFICATES_FOLDER"],
            cert.user.username,
            cert.category.name,
            cert.cert_code,
            completed_in_cat,
        )

    return send_from_directory(
        current_app.config["CERTIFICATES_FOLDER"], cert.file_path,
        as_attachment=False, mimetype="application/pdf"
    )
