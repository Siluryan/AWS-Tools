import argparse
import boto3

regions = ['us-east-1', 'sa-east-1']

def parse_lambda_names(lambda_names):
    if lambda_names:
        return lambda_names
    else:
        return []

def rollback_lambdas(lambda_names):
    for region in regions:
        lambda_client = boto3.client('lambda', region_name=region)
        iam_client = boto3.client('iam', region_name=region)

        functions = []
        marker = None

        if lambda_names:
            for function_name in lambda_names:
                response = lambda_client.list_functions()

                if 'Functions' in response:
                    functions += [f for f in response['Functions'] if f['FunctionName'] == function_name]
        else:
            while True:
                if marker:
                    response = lambda_client.list_functions(Marker=marker)
                else:
                    response = lambda_client.list_functions()

                functions += response['Functions']

                if 'NextMarker' in response:
                    marker = response['NextMarker']
                else:
                    break

        for function in functions:
            function_name = function['FunctionName']

            try:
                response = lambda_client.get_function(FunctionName=function_name)
                current_role_arn = response['Configuration']['Role']
                current_role_name = current_role_arn.split('/')[-1]

                response = lambda_client.list_tags(Resource=function['FunctionArn'])
                tags = response.get('Tags', {})

                if 'IAM Original Role' in tags:
                    original_role_name = tags['IAM Original Role']
                    if current_role_name != original_role_name:
                        response = iam_client.get_role(RoleName=original_role_name)
                        new_role_arn = response['Role']['Arn']
                        lambda_client.update_function_configuration(FunctionName=function_name, Role=new_role_arn)
                        print(f"Execution role of Lambda function '{function_name}' updated to '{original_role_name}'")

                tags_to_remove = ['Quarantine', 'dateToArchive']
                for tag in tags_to_remove:
                    if tag in tags:
                        lambda_client.untag_resource(Resource=function['FunctionArn'], TagKeys=[tag])
                        print(f"Removed the tag '{tag}' from Lambda function: {function_name}")
                    else:
                        print(f"The tag '{tag}' was not found in Lambda function: {function_name}")

            except Exception as e:
                print(f"Error updating Lambda function '{function_name}': {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update execution role and remove specific tags from AWS Lambda functions.')
    parser.add_argument('--all', action='store_true', help='Update execution role and remove tags from all Lambda functions')
    parser.add_argument('lambda_names', nargs='*', help='Lambda function names i.e. lambda1 lambda2')

    args = parser.parse_args()

    if args.all and args.lambda_names:
        print("Please provide either the --all flag or specific Lambda function names, not both.")
    elif args.all:
        rollback_lambdas(lambda_names=None)
    elif args.lambda_names:
        lambda_names = parse_lambda_names(args.lambda_names)
        rollback_lambdas(lambda_names)
    else:
        print('Please provide valid options. Use --help for more information.')
