import os
from flask import Flask
from .database import init_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "portfolio-secret-key-2024")
    os.makedirs(DATA_DIR, exist_ok=True)
    app.config["DATABASE"] = os.path.join(DATA_DIR, "portfolio.db")
    init_db(app.config["DATABASE"])
    from .routes import main
    app.register_blueprint(main)
    return app
