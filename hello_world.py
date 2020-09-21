import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(f"hello\n{str(event['requestContext']['identity'])}\n{str(context)}")
    }