import logging

def get_logger(name):
    return logging.getLogger("django_app_ml." + name)