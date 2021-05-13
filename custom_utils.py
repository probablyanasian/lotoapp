import string
import secrets

alphabet = string.ascii_letters + string.digits

def random_id(length: int) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))