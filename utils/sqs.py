import json

import boto3
from configs import AWS_REGION, SQS_NAME

sqs_resource = boto3.resource("sqs", region_name=AWS_REGION)

queue = sqs_resource.get_queue_by_name(QueueName=SQS_NAME)


def send_sqs(data=None):
    if not data:
        data = {}

    try:
        queue.send_message(MessageBody=json.dumps(data), DelaySeconds=0)
    except Exception as e:
        pass
