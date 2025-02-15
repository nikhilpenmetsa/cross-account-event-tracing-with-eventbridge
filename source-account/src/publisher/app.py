import json
import os
import boto3
from datetime import datetime
from aws_xray_sdk.core import patch_all
from aws_xray_sdk.core import xray_recorder

# Patch all supported libraries for X-Ray tracing
patch_all()

def lambda_handler(event, context):
    # Initialize EventBridge client
    events_client = boto3.client('events')
    
    try:
        # Create subsegment properly
        subsegment = xray_recorder.begin_subsegment('PublishEventToEventBridge')
        
        # Get the event bus name from environment variable
        event_bus_name = os.environ['EVENT_BUS_NAME']
        
        # Extract type from request body
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        should_forward = body.get('forward', False)
        
        # Create the event
        event_detail = {
            "timestamp": datetime.utcnow().isoformat(),
            "requestData": event,
            "type": "forward" if should_forward else "standard"
        }
        
        # Put the event to EventBridge
        response = events_client.put_events(
            Entries=[
                {
                    'Source': 'custom.events',
                    'DetailType': 'CustomEvent',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': event_bus_name
                }
            ]
        )
        
        # Add metadata to the subsegment
        if subsegment:
            subsegment.put_metadata(
                'EventBridge Response', 
                {'EventId': response['Entries'][0]['EventId']}
            )
        
        # Close the subsegment
        xray_recorder.end_subsegment()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Event published successfully',
                'eventId': response['Entries'][0]['EventId'],
                'forwarded': should_forward
            })
        }
        
    except Exception as e:
        # Add error to X-Ray trace if subsegment exists
        if xray_recorder.current_subsegment():
            xray_recorder.current_subsegment().put_metadata(
                'Error', 
                {'message': str(e)}
            )
            xray_recorder.end_subsegment()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
