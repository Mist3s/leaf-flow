import boto3
from botocore.config import Config

from leaf_flow.config import settings


def make_s3_client():
    endpoint = settings.S3_ENDPOINT
    access_key = settings.S3_ACCESS_KEY
    secret_key = settings.S3_SECRET_KEY
    region = settings.S3_REGION
    use_ssl = settings.S3_USE_SSL

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        use_ssl=use_ssl,
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=5,
            read_timeout=120,
        ),
    )
