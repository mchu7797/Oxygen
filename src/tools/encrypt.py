from secrets import token_urlsafe
from random import randint

import requests

from src.config import TURNSTILE_PRIVATE_KEY, TURNSTILE_ENDPOINT


def make_new_password_token():
    # 1Byte = 1.3 Character
    return token_urlsafe(15)


def make_email_auth_token():
    # 1Byte = 1.3 Character
    return token_urlsafe(12)


def check_turnstile_auth(token, remote_ip):
    turnstile_auth_data = {
        "response": token,
        "remoteip": remote_ip,
        "secret": TURNSTILE_PRIVATE_KEY,
    }
    response = requests.post(TURNSTILE_ENDPOINT, data=turnstile_auth_data)

    if response.json()["success"]:
        return True

    return False


def mask_email(email):
    parts = email.split("@")
    if len(parts) != 2:
        return None

    username, domain = parts

    if len(username) <= 4:
        visible_length = 1
    else:
        visible_length = randint(2, len(username) // 2)

    masked_length = randint(3, 6)
    masked_username = username[:visible_length] + "*" * masked_length

    return f"{masked_username}@{domain}"
