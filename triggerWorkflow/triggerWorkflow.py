import json
import requests

def handler(event, context):
    url = "https://api.github.com/repos/REPO_OWNER/REPO_NAME/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer ghp_000000000000000000000",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "event_type": "Deploy - EVENT",
        "client_payload": {
            "unit": False,
            "integration": True
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.text)
