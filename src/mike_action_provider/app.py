import logging

from flask import Flask
from globus_action_provider_tools.flask.helpers import assign_json_provider

from mike_action_provider.blueprint import aptb
from mike_action_provider.config import get_config
from mike_action_provider.logging import setup_logging


def create_app():
    # Set up logging
    setup_logging()

    app = Flask(__name__)

    assign_json_provider(app)
    app.logger.setLevel(logging.DEBUG)

    # Load app configuration
    config = get_config()
    app.config.from_object(config)

    # Register blueprints
    app.register_blueprint(aptb)

    @app.route("/ping")
    def ping():
        return {"message": "pong"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
