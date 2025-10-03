import os
import logging
# 🔑 Added datetime import for the context processor fix 🔑
import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
bootstrap = Bootstrap()

login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'


def create_app(config_name='default'):
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    app = Flask(
        __name__,
        root_path=base_dir,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates')
    )

    app.config.from_object(config_by_name[config_name])

    # Initialize all extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)  # Flask-Bootstrap is now correctly initialized

    from backend.models.users import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/ngo_platform.log'),
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NGO Platform startup')

    # Register blueprints (routes)
    from .routes.home import home as home_blueprint
    app.register_blueprint(home_blueprint)

    from .routes.search import search as search_blueprint
    app.register_blueprint(search_blueprint, url_prefix='/search')

    from .routes.registration import registration as reg_blueprint
    app.register_blueprint(reg_blueprint)

    from .routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .routes.donations import donations as donations_blueprint
    app.register_blueprint(donations_blueprint)

    # 🔑 FIX: Context Processor to make 'now' (datetime object) globally available 🔑
    @app.context_processor
    def inject_global_variables():
        """Makes the 'now' datetime object available to all templates."""
        return dict(
            now=datetime.datetime.now()
        )

    # ---------------------------------------------------------------------------------

    return app


from backend.models import users, temp_ngos, verified_ngos, rejected_ngos
from backend.models import payments, successful_payments, failed_payments