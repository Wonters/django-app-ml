from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


def validate_url_or_s3(value):
    """Validate that the value is either a valid URL or a valid S3 URL."""
    if value.startswith('s3://'):
        # Basic S3 URL validation
        if len(value) < 6 or '/' not in value[5:]:
            raise ValidationError('Invalid S3 URL format. Expected: s3://bucket-name/path')
    else:
        # Use Django's built-in URL validator for HTTP/HTTPS URLs
        url_validator = URLValidator()
        url_validator(value) 