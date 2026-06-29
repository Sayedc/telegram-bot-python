import random
from datetime import datetime

from utils.constants import (
    STICKERS,
    PROCESSING_TEXTS,
    SUCCESS_TEXTS,
    ERROR_TEXTS,
    WELCOME_RESPONSES
)

def get_random_sticker(category):
    return random.choice(STICKERS.get(category, ["🎉"]))

def get_random_processing_text(name):
    return random.choice(PROCESSING_TEXTS).format(name=name)

def get_random_success_text():
    return random.choice(SUCCESS_TEXTS)

def get_random_error_text():
    return random.choice(ERROR_TEXTS)

def get_response(responses, name=None):
    text = responses[datetime.now().second % len(responses)]
    return text.format(name=name) if name else text
