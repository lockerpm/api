import boto3

from django.conf import settings


class SQSService:
    def __init__(self, region_name=settings.AWS_SQS_REGION_NAME, queue_url=settings.AWS_SQS_URL,
                 access_key=settings.AWS_ACCESS_KEY_ID, secret_key=settings.AWS_SECRET_ACCESS_KEY):
        self.service = 'sqs'
        self.region_name = region_name
        self.queue_url = queue_url
        self.access_key = access_key
        self.secret_key = secret_key

    @property
    def client(self):
        return boto3.resource(
            self.service,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name
        ).Queue(self.queue_url)

    def send_message(self, message_body, message_attributes=None):
        if message_attributes is None:
            message_attributes = dict()
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            DelaySeconds=10,
            MessageAttributes=message_attributes,
            MessageBody=message_body
        )
        # print("SQS response: ", response)
        return response['MessageId']


sqs_service = SQSService()
