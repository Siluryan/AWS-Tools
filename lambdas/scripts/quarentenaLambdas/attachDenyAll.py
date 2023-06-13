import logging
import boto3

REGION_NAME = 'us-east-1'
LAMBDA_FUNCTIONS = ['ambientes-sem-destroy-homolog-prod-filtrarAmbientesHomolog']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


add_deny_all_policy_to_lambda_roles(LAMBDA_FUNCTIONS, REGION_NAME)