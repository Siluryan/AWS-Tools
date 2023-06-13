import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def filter_not_in_quarantine_lambdas(unused_days, session_lambda_client, session_iam_client, session_cloudwatch_client):
    response = session_lambda_client.list_functions()
    lambdas = response['Functions']

    lambdas_not_in_quarantine = []

    six_months_ago = datetime.now() - timedelta(days=unused_days)
    six_months_ago = six_months_ago.replace(tzinfo=None)

    for lmd in lambdas:
        function_name = lmd['FunctionName']
        role_arn = lmd['Role']
        create_date = None

        try:
            response = session_iam_client.get_role(RoleName=role_arn.split('/')[-1])
            create_date = response['Role']['CreateDate']

        except Exception as e:
            logger.error(f"Error getting creation date of IAM role associated with Lambda function {function_name}: {e}")
            continue

        if create_date and create_date.replace(tzinfo=None) <= six_months_ago:
            try:
                response = session_cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=six_months_ago,
                    EndTime=datetime.now(),
                    Period=2592000,
                    Statistics=['SampleCount']
                )

                if not response['Datapoints']:
                    lambdas_not_in_quarantine.append(function_name)

            except Exception as e:
                logger.error(f"Error getting invocation metrics for Lambda function {function_name}: {e}")

    return lambdas_not_in_quarantine

def create_deny_all_role(iam_client):
    deny_all_role_name = "AWSDenyAllRole"

    try:
        iam_client.get_role(RoleName=deny_all_role_name)
        logger.info(f"The {deny_all_role_name} role already exists. Continuing with the script.")
    except iam_client.exceptions.NoSuchEntityException:
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }

        create_role_response = iam_client.create_role(
            RoleName=deny_all_role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description="Role for deny all Lambda functions"
        )

        role_arn = create_role_response['Role']['Arn']

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*"
            }]
        }

        iam_client.put_role_policy(
            RoleName=deny_all_role_name,
            PolicyName="DenyAllPolicy",
            PolicyDocument=json.dumps(policy_document)
        )

        logger.info(f"The {deny_all_role_name} role has been created with ARN: {role_arn}")

def quarentine_lambda(account_id, function_name, boto3_lambda_client):
    try:
        response = boto3_lambda_client.get_function(FunctionName=function_name)
        current_role_arn = response['Configuration']['Role']
        current_role_name = current_role_arn.split('/')[-1]

        existing_tags_response = boto3_lambda_client.list_tags(Resource=response['Configuration']['FunctionArn'])
        existing_tags = existing_tags_response.get('Tags', {})

        tag_key = 'IAM Original Role'
        if tag_key in existing_tags:
            logger.info(f"The '{tag_key}' tag already exists for Lambda function {function_name}. Skipping tag addition.")
        else:
            original_role_name = current_role_name
            tag_value = original_role_name

            boto3_lambda_client.tag_resource(Resource=response['Configuration']['FunctionArn'], Tags={tag_key: tag_value})
            logger.info(f"Tag '{tag_key}': '{tag_value}' added to Lambda function {function_name}.")

        tag_key = 'Quarantine'
        if tag_key not in existing_tags:
            boto3_lambda_client.tag_resource(Resource=response['Configuration']['FunctionArn'], Tags={tag_key: 'true'})
            logger.info(f"Tag '{tag_key}': 'true' added to Lambda function {function_name}.")
        else:
            logger.info(f"Tag '{tag_key}' already exists for Lambda function {function_name}. Skipping tag addition.")

        date_to_archive_key = 'dateToArchive'
        six_months_from_now = datetime.now() + timedelta(days=180)
        six_months_from_now_str = six_months_from_now.strftime('%Y-%m-%d')

        if date_to_archive_key not in existing_tags:
            boto3_lambda_client.tag_resource(Resource=response['Configuration']['FunctionArn'], Tags={date_to_archive_key: six_months_from_now_str})
            logger.info(f"Tag '{date_to_archive_key}': '{six_months_from_now_str}' added to Lambda function {function_name}.")
        else:
            logger.info(f"Tag '{date_to_archive_key}' already exists for Lambda function {function_name}. Skipping tag addition.")

        deny_all_role_name = f"arn:aws:iam::{account_id}:role/AWSDenyAllRole" 

        if deny_all_role_name != current_role_name:
            boto3_lambda_client.update_function_configuration(
                FunctionName=function_name,
                Role=deny_all_role_name
            )

            statement_id = f"AllowLambdaInvoke-{function_name[:35]}"

            try:
                boto3_lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=statement_id,
                    Action="lambda:InvokeFunction",
                    Principal="*",
                    SourceArn=current_role_arn
                )
            except boto3_lambda_client.exceptions.ResourceConflictException:
                logger.info(f"A permissão de invocação da função Lambda {function_name} já existe para a função IAM Role {deny_all_role_name}.")

            logger.info(f"A função IAM Role {deny_all_role_name} foi associada com sucesso à função Lambda {function_name}.")

    except Exception as e:
        logger.error(f"Ocorreu um erro ao adicionar a política 'deny all' à nova função exclusiva para a função Lambda {function_name}: {e}")

def handler(event, context):
    region = 'us-east-1'
    account_id = 1000000000

    unused_days = 180

    session = boto3.Session(region_name=region)
    session_iam_client = session.client('iam')
    session_lambda_client = session.client('lambda')
    session_cloudwatch_client = session.client('cloudwatch')
    boto3_lambda_client = boto3.client('lambda', region_name=region)

    create_deny_all_role(session_iam_client)

    lambdas_not_in_quarantine = filter_not_in_quarantine_lambdas(unused_days, session_lambda_client, session_iam_client, session_cloudwatch_client)
    
    for lambda_function in lambdas_not_in_quarantine:
        quarentine_lambda(account_id, lambda_function, boto3_lambda_client)