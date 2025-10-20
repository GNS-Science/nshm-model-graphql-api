# DEVELOPMENT

### Environment setup

 - clone the repo
 - check/install a recent node version >=22
   `nvm use 22`

- setup python env
```
pyenv local 3.12
poetry env use 3.12
```

setup yarn 2 ...
```


yarn install
```

Now `yarn sls info` should print something like ...

```
$ sls info
Running "serverless" from node_modules
Environment: darwin, node 22.16.0, framework 3.40.0 (local), plugin 7.2.3, SDK 4.5.1
Credentials: Local, "default" profile
Docs:        docs.serverless.com
Support:     forum.serverless.com
Bugs:        github.com/serverless/serverless/issue

```
You'll problably see an error, if your AWS credentials are not those required for SLS.

## TESTING

### Run API locally
```
ENABLE_METRICS=0 poetry run yarn sls wsgi serve
```

## Auditing requirements packages

NB this is now included in tox:audit step

```
poetry export --all-groups --output audit.txt
poetry run pip-audit -r audit.txt -s pypi --require-hashes
poetry run pip-audit -r audit.txt -s osv --require-hashes

poetry show {package-name}
```

### `safety` requires user login registration, but seems closer to dependabot in detections.
```
poetry run safety scan
```

### Node
```
yarn npm audit -R
yarn why {package-name}
yarn upgrade-interactive
```

## DEPLOY DEV service

```
AWS_PROFILE=**** poetry run yarn sls deploy --region ap-southeast-2 --stage dev
```

### API Feature tests
`$>poetry run pytest` should just work.


