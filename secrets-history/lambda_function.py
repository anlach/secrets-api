import boto3
import json
import base64
from boto3.dynamodb.types import Binary

print('Loading function')
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('secrets-db')


def lambda_handler(event, context):
    '''
    Print 100 items.
    '''
    output = []
    for item in table.scan(Limit=100)['Items']:
        output_item = {}
        for k, v in item.items():
            if isinstance(v, Binary):
                output_item[k] = base64.b64encode(bytes(v)).decode()
            else:
                output_item[k] = v
        output.append(output_item)
    return {
        'statusCode': '200',
        'body': json.dumps(output),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

