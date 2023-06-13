import boto3

def update_execution_role_based_on_tag():
    lambda_client = boto3.client('lambda')

    response = lambda_client.list_functions(MaxItems=50)
    lambdas = response['Functions']

    while 'NextMarker' in response:
        response = lambda_client.list_functions(Marker=response['NextMarker'], MaxItems=50)
        lambdas.extend(response['Functions'])

    for lmd in lambdas:
        function_name = lmd['FunctionName']

        response = lambda_client.list_tags(Resource=lmd['FunctionArn'])
        tags = response.get('Tags', {})

        if 'IAM Original Role' in tags:
            original_role_name = tags['IAM Original Role']

            response = lambda_client.get_function(FunctionName=function_name)
            current_role_arn = response['Configuration']['Role']
            current_role_name = current_role_arn.split('/')[-1]

            if current_role_name != original_role_name:
                try:
                    iam_client = boto3.client('iam')
                    response = iam_client.get_role(RoleName=original_role_name)
                    new_role_arn = response['Role']['Arn']

                    lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Role=new_role_arn
                    )
                    print(f"Execution role of Lambda function '{function_name}' updated to '{original_role_name}'")
                except Exception as e:
                    print(f"Error updating execution role of Lambda function '{function_name}': {e}")

if __name__ == "__main__":
    update_execution_role_based_on_tag()
