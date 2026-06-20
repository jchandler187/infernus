import os
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.secret_key = os.environ.get("SECRET_KEY", "dev")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from routes import register_routes
    register_routes(app)

    return app


if __name__ == "__main__":
    import config
    create_app().run(host="0.0.0.0", port=config.PORT, debug=False)
