from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# For example, my-test-domain.us-east-1.es.amazonaws.com
ES_HOST = 'https://search-nshm-model-opensearch-poc-fz3qmvqjus5clpyxgvfju3c4fq.ap-southeast-2.es.amazonaws.com'
ES_REGION = 'ap-southeast-2' # e.g. us-west-1
IS_OFFLINE = None
awsauth = None

if not IS_OFFLINE:
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            ES_REGION,
            'es',
            session_token=credentials.token) 
    
es = Elasticsearch(
    hosts=[ES_HOST],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

print(es.info())