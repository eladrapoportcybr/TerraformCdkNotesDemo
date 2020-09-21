import json
import boto3
import datetime


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    s3.Object('eladr-terraform-cdk-demo-bucket',
              f"{str(event['requestContext']['identity'].get('sourceIp'))}_{int(datetime.datetime.now().timestamp() * 1000)}.txt") \
        .put(Body=str(event))
    return {
        'statusCode': 200,
        'body': f"Hello {str(event['requestContext']['identity'].get('sourceIp'))}!"
    }
