import os
import glob
import boto3
from botocore.exceptions import ClientError

def upload_wheel_to_s3():
    # Get AWS credentials from environment variables
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION')
    bucket_name = os.environ.get('S3_BUCKET')

    if not all([aws_access_key, aws_secret_key, aws_region, bucket_name]):
        raise ValueError("Missing required AWS environment variables")

    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )

    # Find the wheel file
    wheel_files = glob.glob('dist/*.whl')
    if not wheel_files:
        raise FileNotFoundError("No wheel file found in dist/ directory")

    wheel_file = wheel_files[0]  # Take the first wheel file found
    file_name = os.path.basename(wheel_file)
    s3_key = f'wheels/{file_name}'

    try:
        # Upload the file
        s3_client.upload_file(
            wheel_file,
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': 'application/octet-stream'}
        )
        print(f"Successfully uploaded {file_name} to s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        raise

if __name__ == '__main__':
    upload_wheel_to_s3() 