import ast
import traceback
import urllib.parse
from datetime import datetime
from typing import Optional
import boto3
from botocore.config import Config
from botocore.errorfactory import ClientError
from botocore.signers import CloudFrontSigner
# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings

from shared.log.cylog import CyLog
from shared.utils.app import now

DEFAULT_S3_EXPIRED = 120


class S3Service:
    def __init__(self, access_key: str = None, secret_key: str = None, region: str = None, endpoint_url: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.endpoint_url = endpoint_url
        self.service = 's3'
        self.config = Config(
            signature_version='s3v4',
            s3={'addressing_style': "virtual"},
            retries={
                "max_attempts": 1,  # this includes the initial attempt to get the email
                "mode": "standard",
            }
        )

    @property
    def client(self):
        return boto3.client(
            self.service,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=self.config,
        )

    def upload_bytes_object(self, key, io_bytes, acl="private", bucket=settings.AWS_S3_BUCKET):
        """
        Upload file to s3
        :param key: S3 key (path)
        :param io_bytes: IO stream
        :param acl: public-read or private?
        :param bucket: The bucket name
        :return:
        """
        try:
            # io_bytes.seek(0)
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=io_bytes.read(),
                ACL=acl,
                # Tagging='document_type=invoice'
            )
            return key
        except:
            tb = traceback.format_exc()
            CyLog.error(**{"message": "Upload IO to s3 error: {}".format(tb)})

    def gen_one_time_url(self, file_path: str, is_cdn=False, source: str = settings.AWS_S3_BUCKET,
                         **kwargs) -> Optional[str]:
        """
        Generate one-time url
        :param file_path:
        :param is_cdn:
        :param source:
        :param kwargs:
        :return:
        """
        if not file_path:
            return
        # if is_cdn:
        #     expired = kwargs.get("expired", DEFAULT_S3_EXPIRED)
        #     expire_date = datetime.utcfromtimestamp(now() + expired)  # 1 minute
        #     cloudfront_signer = CloudFrontSigner(settings.AWS_CLOUDFRONT_PUBLIC_KEY_ID, self._rsa_signer)
        #     if not file_path.startswith("https://") and not file_path.startswith("http://"):
        #         file_path = "{}/{}".format(settings.CDN_ATTACHMENT_URL, file_path)
        #
        #     # Addition headers
        #     response_content_disposition = kwargs.get("response_content_disposition")
        #     if response_content_disposition:
        #         encode_response_content_disposition = urllib.parse.unquote(
        #             response_content_disposition
        #         ).replace("+", "%20")
        #         file_path = "{}?response-content-disposition={}".format(file_path, encode_response_content_disposition)
        #
        #     # Create a signed url that will be valid until the specific expiry date provided using a canned policy.
        #     signed_url = cloudfront_signer.generate_presigned_url(file_path, date_less_than=expire_date)
        #     return signed_url
        #
        # else:
        expired_in = kwargs.get("expired", DEFAULT_S3_EXPIRED)
        response_content_disposition = kwargs.get("response_content_disposition", None)
        bucket_params = {
            'Bucket': source,
            'Key': file_path,
        }
        if response_content_disposition:
            bucket_params.update({"ResponseContentDisposition": response_content_disposition})
        pre_signed_params = {
            "Params": bucket_params,
            "ExpiresIn": expired_in
        }
        url = self.client.generate_presigned_url(
            'get_object',
            **pre_signed_params
        )
        # url = url.replace("https://{}.s3.amazonaws.com".format(source), settings.CDN_ATTACHMENT_URL)
        return url

    # @staticmethod
    # def _rsa_signer(message):
    #     credentials_json_data = ast.literal_eval(str(settings.AWS_CLOUDFRONT_PRIVATE_KEY))
    #     secret = bytes(credentials_json_data.get("secret"), 'utf-8')
    #     private_key = serialization.load_pem_private_key(
    #         secret,
    #         password=None,
    #         backend=default_backend()
    #     )
    #     return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())


s3_service = S3Service(
    access_key=settings.AWS_S3_ACCESS_KEY,
    secret_key=settings.AWS_S3_SECRET_KEY,
    region=settings.AWS_S3_REGION_NAME,
)
