import os
from flask import Flask
from .database import init_db

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "portfolio-secret-key-2024"

    # Use Supabase PostgreSQL on Render, SQLite locally
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # Render + Supabase — use PostgreSQL
        app.config["DATABASE_URL"] = database_url
        app.config["DB_TYPE"] = "postgres"
    else:
        # Local development — use SQLite
        os.makedirs(app.instance_path, exist_ok=True)
        app.config["DATABASE_URL"] = os.path.join(app.instance_path, "portfolio.db")
        app.config["DB_TYPE"] = "sqlite"

    init_db(app.config["DATABASE_URL"], app.config["DB_TYPE"])

    from .routes import main
    app.register_blueprint(main)

    return app
