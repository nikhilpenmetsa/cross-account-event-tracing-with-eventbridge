import os
import json
import uuid
from datetime import datetime
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    #print(event)
    try:
        item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'message': event['detail']['requestData']['body'],
            'eventDetails': event['detail']
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Event processed successfully')
        }
    except Exception as e:
        print(f'Error: {str(e)}')
        raise
