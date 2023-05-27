import boto3
import logging
from datetime import datetime, timedelta

region = 'us-east-1'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_unused_lambdas(region):
    session = boto3.Session(region_name=region)
    lambda_client = session.client('lambda')
    cloudwatch_client = session.client('cloudwatch')

    response = lambda_client.list_functions()
    lambdas = response['Functions']

    unused_lambdas = []

    six_months_ago = datetime.now() - timedelta(days=180)
    six_months_ago = six_months_ago.replace(tzinfo=None)

    for lmd in lambdas:
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'invocations',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/Lambda',
                            'MetricName': 'Invocations',
                            'Dimensions': [
                                {
                                    'Name': 'FunctionName',
                                    'Value': lmd['FunctionName']
                                }
                            ]
                        },
                        'Period': 2592000, 
                        'Stat': 'SampleCount'
                    }
                }
            ],
            StartTime=six_months_ago,
            EndTime=datetime.now(),
        )

        if not response['MetricDataResults'][0]['Values']:
            last_modified = lmd['LastModified']
            last_modified_datetime = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%f%z")
            last_modified_datetime = last_modified_datetime.replace(tzinfo=None)  

            if last_modified_datetime <= six_months_ago:
                unused_lambdas.append(lmd['FunctionName'])

    return unused_lambdas

unused_lambdas = get_unused_lambdas(region)

def add_deny_all_policy_to_lambda_roles(function_names, region):
    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam', region_name=region)

    for function_name in function_names:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            role_arn = response['Configuration']['Role']

            policy_arn = 'arn:aws:iam::aws:policy/AWSDenyAll'
            iam_client.attach_role_policy(RoleName=role_arn.split('/')[-1], PolicyArn=policy_arn)

            logger.info(f"Política 'deny all' adicionada com sucesso à função IAM Role associada à função Lambda {function_name}")

        except Exception as e:
            logger.error(f"Ocorreu um erro ao adicionar a política 'deny all' à função IAM Role associada à função Lambda {function_name}: {e}")

add_deny_all_policy_to_lambda_roles(unused_lambdas, region)