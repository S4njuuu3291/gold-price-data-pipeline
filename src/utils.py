import google.cloud.secretmanager as secretmanager

PROJECT_ID = "gold-price-alert-488703"
TOPIC_ID = "gold-price-alert-488703-topic"

def get_secret_value(project_id, secret_name, version="latest"):
    """
    Retrieve the value of a secret from Google Cloud Secret Manager.

    Args:
        project_id (str): The ID of the GCP project.
        secret_name (str): The name of the secret.
        version (str): The version of the secret to retrieve (default is "latest").

    Returns:
        str: The value of the secret, or None if an error occurs.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
        response = client.access_secret_version(request={"name": secret_path})
        secret_value = response.payload.data.decode("UTF-8")
        return secret_value
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None
    
    