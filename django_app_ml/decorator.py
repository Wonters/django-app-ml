import logging
import time

logger = logging.getLogger('scoring_model')

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        logger.info(f"{func.__name__}: {time.time() - start}")
        return result
    return wrapper