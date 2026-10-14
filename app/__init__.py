from flask import Flask

from app.config import load_config


def create_app(test_config=None):
    """Flask app factory. Boots without credentials; they are checked only when a call is placed."""
    app = Flask(__name__)
    app.config.update(load_config())
    if test_config is not None:
        app.config.update(test_config)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
