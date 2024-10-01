import validators
from urllib.parse import urlparse


def validate_url(url):
    return validators.url(url)


def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return normalized_url
