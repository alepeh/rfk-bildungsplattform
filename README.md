# rfk-bildungsplattform

## Generate graphical model overview
The applications for which an overview is generated are configured in settings.py
```
$ ./manage.py graph_models -o bildungsplattform_model.png
```

## Configure an s3 compliant storage user supplied blob data
Install django-storages

```
pip install django-storages
pip install boto3
```

In settings.py add the following 
```
STORAGES = {
    "default": "storages.backends.s3boto3.S3Boto3Storage",
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```
static files will still be served from the default static file storage

Add the following variables to settings.py, those will be picked up by django-storages

```
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
```

Set the media url to the custom s3 domain in settings.py

```
MEDIA_URL = AWS_S3_CUSTOM_DOMAIN
```

## Adding content

### Pages and Page templates
Each page is represented as a Django model and therefore also as a table in the database.
You can use any django field class, also from 3rd party apps.


