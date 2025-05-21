from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class ScalewayObjectStorage(S3Boto3Storage):
    access_key = settings.SCALEWAY_ACCESS_KEY
    secret_key = settings.SCALEWAY_SECRET_KEY
    bucket_name = settings.SCALEWAY_BUCKET_NAME
    region_name = settings.SCALEWAY_REGION
    endpoint_url = f'https://s3.{settings.SCALEWAY_REGION}.scw.cloud'
    object_parameters = {
        'ACL': 'public-read'
    }
    querystring_auth = False