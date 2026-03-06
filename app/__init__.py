from markupsafe import Markup
from pathlib import Path

from flask import Flask
from markdown import markdown

from app.activities.routes import activities_bp
from app.auth.routes import auth_bp
from app.challenges.routes import challenges_bp
from app.comments.routes import comments_bp
from app.config import Config
from app.extensions import csrf, db, login_manager, migrate, limiter
from app.main.routes import main_bp
from app.notifications.routes import notifications_bp
from app.reactions.routes import reactions_bp
from app.teams.routes import teams_bp
import bleach


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(config_class)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    register_extensions(app)
    register_template_helpers(app)
    register_blueprints(app)

    return app


def register_template_helpers(app):
    @app.template_filter("markdown")
    def markdown_filter(value):
        if not value:
            return ""

        html = markdown(
            value,
            extensions=["fenced_code", "tables", "sane_lists"],
            output_format="html5",
        )
        safe_html = bleach.clean(
            html,
            tags=app.config["MARKDOWN_SAFE_TAGS"],
            attributes=app.config["MARKDOWN_SAFE_ATTRIBUTES"],
            protocols=app.config["MARKDOWN_SAFE_PROTOCOLS"],
            strip=True,
        )

        return Markup(safe_html)


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(reactions_bp)
    app.register_blueprint(teams_bp)
