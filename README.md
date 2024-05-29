
# nshm-model-graphql-api

A GRAPHQL API for the nzshm-model libary .

Using Flask with Serverless framework to operate as a AWS Lambda API.

The graphql API documentation is served by default from the service root.


## Getting started

```
poetry install
npm install --save serverless
npm install --save serverless-python-requirements
npm install --save serverless-wsgi
npm install --save serverless-plugin-warmup
```

## Some Useful commands

```
poetry shell
npx sls wsgi serve
```

