import secrets


def make_new_password_token():
    # 1Byte = 1.3 Character
    return token_urlsafe(15)
