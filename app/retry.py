import random
import time
from functools import wraps

from openai import RateLimitError


def with_backoff(max_retries: int = 5, base_delay: float = 1.0):
    """Retries the wrapped call with exponential backoff + jitter on OpenAI 429 rate-limit
    errors. Re-raises once max_retries is exhausted."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2**attempt) + random.uniform(0, base_delay)
                    time.sleep(delay)

        return wrapper

    return decorator
