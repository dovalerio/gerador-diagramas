"""
Main application entry point.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv(override=False)  # must run before any project import reads os.getenv

from flask import Flask
from waitress import serve

from api.routes import api_bp
from config.settings import Config, UPLOAD_FOLDER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(api_bp)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    return app


if __name__ == '__main__':
    app = create_app()

    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        print("Servidor iniciado em http://0.0.0.0:5000")
        serve(app, host='0.0.0.0', port=5000)
