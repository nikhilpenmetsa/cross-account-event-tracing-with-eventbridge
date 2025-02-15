# Cross-Account Event-Driven Architecture with AWS EventBridge

This project implements a cross-account event-driven architecture using AWS EventBridge, Lambda, and API Gateway.
It demonstrates how to publish events from a source account and process them in a destination account.

The architecture consists of two main components: a source account that publishes events and a destination account that processes forwarded events.
Events are published through an API Gateway endpoint, processed by a Lambda function, and then sent to an EventBridge custom event bus.
Depending on the event type, they can be forwarded to a destination account for further processing.

## Repository Structure

```
.
├── destination-account
│   ├── samconfig.toml
│   ├── src
│   │   └── app.py
│   └── template.yaml
└── source-account
    ├── samconfig.toml
    ├── src
    │   └── publisher
    │       ├── app.py
    │       └── requirements.txt
    └── template.yaml
```

### Key Files:

- `destination-account/template.yaml`: CloudFormation template for the destination account infrastructure
- `destination-account/src/app.py`: Lambda function for processing events in the destination account
- `source-account/template.yaml`: CloudFormation template for the source account infrastructure
- `source-account/src/publisher/app.py`: Lambda function for publishing events in the source account
- `source-account/src/publisher/requirements.txt`: Python dependencies for the publisher function

### Integration Points:

- API Gateway: Endpoint for publishing events in the source account
- EventBridge: Custom event buses in both source and destination accounts
- Lambda: Functions for publishing and processing events
- DynamoDB: Table for storing processed events in the destination account

## Usage Instructions

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.13 or later
- Two AWS accounts: one for source and one for destination

### Installation

1. Clone the repository:
   ```
   git clone git@github.com:nikhilpenmetsa/cross-account-event-tracing-with-eventbridge.git
   cd eventbridge
   ```

2. Deploy the destination account stack:
   ```
   cd destination-account
   sam deploy --guided --profile eb-destination   ```
   Follow the prompts and provide the source account ID when asked.

3. Deploy the source account stack:
   ```
   cd ../source-account
   sam deploy --guided --profile eb-source
   ```
   Follow the prompts and provide the destination account ID when asked.

4. Note the API Gateway endpoint URL from the source account stack outputs.

### Publishing Events

To publish an event, send a POST request to the API Gateway endpoint:

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/prod/publish \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, EventBridge!", "forward": true}'
```

Set `"forward": true` to forward the event to the destination account, or `false` to keep it in the source account.

### Monitoring and Troubleshooting

1. Check CloudWatch Logs:
   - Source account: `/aws/events/source-bus-events` and `/aws/events/forwarded-events`
   - Destination account: `/aws/events/destination-bus-events`

2. View processed events:
   - In the destination account, check the `ForwardedEvents` DynamoDB table

3. Enable X-Ray tracing:
   - Both Lambda functions have X-Ray tracing enabled by default
   - Use the AWS X-Ray console to visualize and analyze the request flow

### Common Issues and Solutions

1. Events not appearing in the destination account:
   - Check the EventBridge bus policy in the destination account
   - Verify the IAM role permissions in the source account
   - Ensure the `forward` flag is set to `true` in the request payload

2. API Gateway 5xx errors:
   - Check the Lambda function logs for errors
   - Verify the Lambda function execution role has necessary permissions

3. DynamoDB write failures:
   - Check the Lambda function execution role in the destination account
   - Verify the DynamoDB table name in the environment variables

## Data Flow

1. Client sends a POST request to the API Gateway endpoint in the source account.
2. API Gateway triggers the `PublisherFunction` Lambda in the source account.
3. `PublisherFunction` publishes an event to the source account's custom EventBridge bus.
4. If the event has `"forward": true`, the `ForwardingRule` sends it to the destination account's custom EventBridge bus.
5. In the destination account, the `ForwardEventRule` triggers the `ProcessEventFunction` Lambda.
6. `ProcessEventFunction` processes the event and stores it in the `ForwardedEvents` DynamoDB table.

```
Client -> API Gateway -> PublisherFunction -> Source EventBridge Bus
                                                    |
                                                    v
                                          Destination EventBridge Bus
                                                    |
                                                    v
                                          ProcessEventFunction -> DynamoDB
```

## Infrastructure

### Source Account

- EventBridge:
  - `CustomEventBus`: Custom event bus for source events
  - `EventRule`: Rule for logging all events to CloudWatch
  - `ForwardingRule`: Rule for forwarding events to the destination account
- Lambda:
  - `PublisherFunction`: Publishes events to the custom event bus
- API Gateway:
  - `RestApi`: API for the publish endpoint
- IAM:
  - `EventBridgeForwardingRole`: Role for forwarding events to the destination account
- CloudWatch:
  - `EventLogGroup`: Log group for source bus events
  - `ForwardedEventsLogGroup`: Log group for forwarded events

### Destination Account

- EventBridge:
  - `DestinationCustomBus`: Custom event bus for receiving events
  - `EventLoggingRule`: Rule for logging all received events
  - `ForwardEventRule`: Rule for processing forwarded events
- Lambda:
  - `ProcessEventFunction`: Processes received events and stores them in DynamoDB
- DynamoDB:
  - `EventsTable`: Table for storing processed events
- CloudWatch:
  - `DestinationLogGroup`: Log group for destination bus events