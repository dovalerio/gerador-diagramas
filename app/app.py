"""
Main application entry point.
"""
import os
from dotenv import load_dotenv
from flask import Flask
from waitress import serve

from api.routes import api_bp
from config.settings import Config, UPLOAD_FOLDER

load_dotenv(override=False)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(api_bp)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    return app


if __name__ == '__main__':
    app = create_app()

    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Servidor iniciado em http://0.0.0.0:5000")
        serve(app, host='0.0.0.0', port=5000)
