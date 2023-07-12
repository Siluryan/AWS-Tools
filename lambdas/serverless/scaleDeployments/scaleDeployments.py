import boto3
import os
import subprocess
import urllib.request
import logging
from datetime import datetime, timedelta
import json

deployments_file = "deploymentsToScale.json"

cluster_url = "https://api.k8shomolog.com.br"
parameter_name = "/parameter-k8s"

kubectl_version_url = "https://dl.k8s.io/release/stable.txt"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def download_file(url, output_path):
    with urllib.request.urlopen(url) as response:
        with open(output_path, "wb") as file:
            file.write(response.read())

def scale_deployments(deployments, scale_to_zero):
    kubectl_path = "/tmp/kubectl"
    kubeconfig = "/tmp/kubeconfig"

    with urllib.request.urlopen(kubectl_version_url) as response:
        kubectl_version = response.read().decode("utf-8").strip()

    kubectl_url = f"https://dl.k8s.io/release/{kubectl_version}/bin/linux/amd64/kubectl"

    logger.info(f"Downloading kubectl from {kubectl_url} to {kubectl_path}")
    os.makedirs(os.path.dirname(kubectl_path), exist_ok=True)
    download_file(kubectl_url, kubectl_path)
    os.chmod(kubectl_path, 0o755)

    scale_value = "0" if scale_to_zero else "1"

    for deployment, config in deployments.items():
        namespace = config["namespace"]
        kubectl_command = [
            kubectl_path,
            "--kubeconfig",
            kubeconfig,
            "-n",
            namespace,
            "scale",
            f"deployment/{deployment}",
            f"--replicas={scale_value}"
        ]
        logger.info(f"Running kubectl command: {' '.join(kubectl_command)}")
        subprocess.run(kubectl_command, stderr=subprocess.STDOUT)

def lambda_handler(event, context):
    logger.info("Lambda function triggered")

    with open(deployments_file, "r") as file:
        deployments = json.load(file)

    ssm_client = boto3.client("ssm")
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    secret_value = response["Parameter"]["Value"]

    kubeconfig = "/tmp/kubeconfig"
    with open(kubeconfig, "w", encoding="utf-8") as file:
        file.write(secret_value)

    now = datetime.utcnow() - timedelta(hours=3)
    hour = now.hour

    logger.info(f"Current hour: {hour}")

    if hour >=23 or hour < 7:
        logger.info("Scaling deployments to 0 replicas")
        scale_deployments(deployments, True)
        message = "Deployments scaled to 0"
    elif hour >= 7:
        logger.info("Scaling deployments to 1 replica")
        scale_deployments(deployments, False)
        message = "Deployments scaled to 1"
    else:
        message = "No scaling action needed"

    logger.info(f"Scaling operation complete: {message}")

    return {
        "statusCode": 200,
        "body": message
    }