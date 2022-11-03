from uuid import uuid4


def generate_id(prefix=""):
    if prefix != "":
        prefix += "-"
    return f"{prefix}{str(uuid4())}"
