import boto3

tag_to_remove = 'Quarantine'

def remove_tag_lambda_functions():
    lambda_client = boto3.client('lambda')

    functions = []
    marker = None
    
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
        
        tags = lambda_client.list_tags(Resource=function['FunctionArn'])['Tags']
        if tag_to_remove in tags:
            print(f"Removing the tag {tag_to_remove} from Lambda function: {function_name}")
            lambda_client.untag_resource(Resource=function['FunctionArn'], TagKeys=[tag_to_remove])
        else:
            print(f"The tag {tag_to_remove} was not found in Lambda function: {function_name}")

remove_tag_lambda_functions()