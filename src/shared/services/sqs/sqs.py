import boto3

from django.conf import settings


class SQSService:
    def __init__(self, region_name=settings.AWS_SQS_REGION_NAME, queue_url=settings.AWS_SQS_URL):
        self.service = 'sqs'
        self.region_name = region_name
        self.queue_url = queue_url

    @property
    def client(self):
        return boto3.resource(self.service, region_name=self.region_name).Queue(self.queue_url)

    def send_massage(self, message_body, message_attributes=None):
        if message_attributes is None:
            message_attributes = dict()
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            DelaySeconds=10,
            MessageAttributes=message_attributes,
            MessageBody=message_body
        )
        return response['MessageId']
