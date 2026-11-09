from login_pass import enc

PASSWORD = "0.0080715744432558590.00680735194009530250.0079743265583973550.0092385490615579120.00466789847320820"

_state = {"authenticated": False}


def is_authenticated():
    return _state["authenticated"]


def login(password):
    if not password:
        return False
    if enc(password, 10283) == PASSWORD:
        _state["authenticated"] = True
        return True
    return False


def logout():
    _state["authenticated"] = False