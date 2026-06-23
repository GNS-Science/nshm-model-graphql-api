"""FastAPI + Mangum entry point.

The Lambda handler is `nshm_model_graphql_api.app.handler` (Mangum), wired in
`serverless.yml`. The `/graphql` path is preserved — clients are hardcoded to it.
"""

from fastapi import FastAPI
from mangum import Mangum
from strawberry.fastapi import GraphQLRouter

from nshm_model_graphql_api.schema import schema

app = FastAPI(title="nshm-model-graphql-api")

graphql_app: GraphQLRouter = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# AWS Lambda entry point.
handler = Mangum(app)
