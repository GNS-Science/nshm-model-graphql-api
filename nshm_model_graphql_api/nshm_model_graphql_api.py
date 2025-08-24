"""Main module."""

import logging
import logging.config
import os

import yaml
from flask import Flask
from flask_cors import CORS
from graphql_server.flask.views import GraphQLView

# from nshm_model_graphql_api.library_version_check import log_library_info
from nshm_model_graphql_api.schema import schema_root

LOGGING_CFG = os.getenv("LOGGING_CFG", "nshm_model_graphql_api/logging_aws.yaml")
logger = logging.getLogger(__name__)

# TESTING = os.getenv('TESTING', False)
# if not TESTING:
#     # because in testing, this screws up moto mocking
#     log_library_info(['botocore', 'boto3', 'fiona'])


def create_app():
    """Function that creates our Flask application."""
    app = Flask(__name__)
    CORS(app)

    # app.before_first_request(migrate)

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql",
            schema=schema_root,
            graphiql=True,
        ),
    )

    """
    Setup logging configuration
    ref https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    """
    if os.path.exists(LOGGING_CFG):
        with open(LOGGING_CFG, "rt") as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        print("Warning, no logging config found, using basicConfig(INFO)")
        logging.basicConfig(level=logging.INFO)

    logger.debug("DEBUG logging enabled")
    logger.info("INFO logging enabled")
    logger.warning("WARN logging enabled")
    logger.error("ERROR logging enabled")

    return app


# pragma: no cover
app = create_app()


if __name__ == "__main__":
    app.run()
