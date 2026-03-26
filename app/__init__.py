import os
from flask import Flask
from .database import init_db

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "portfolio-secret-key-2024"

    if os.environ.get("RENDER"):
        db_path = "/tmp/portfolio.db"
    else:
        os.makedirs(app.instance_path, exist_ok=True)
        db_path = os.path.join(app.instance_path, "portfolio.db")

    app.config["DATABASE"] = db_path
    init_db(db_path)

    from .routes import main
    app.register_blueprint(main)

    return app
