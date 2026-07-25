from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """
    Generate a secure hash for the given password.
    """
    return generate_password_hash(password)


def verify_password(hashed_password, password):
    """
    Verify a password against its stored hash.
    """
    return check_password_hash(hashed_password, password)