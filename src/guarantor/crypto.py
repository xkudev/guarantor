from pycoin.symbols.btc import network as BTC


def validate_wif(wif: str):
    """Raises ValueError if given input cannot be used for signing."""
    pass


def validate_message(message: str):
    """Raises ValueError if given input cannot be signed."""
    pass


def validate_digest(digest: str):
    """Raises ValueError if given input not a valid digest."""
    pass


def validate_address(address: str):
    """Raises ValueError if given address not valid."""
    pass


def validate_signature(signature: str):
    """Raises ValueError if given signature not valid."""
    pass


def digest(message: str) -> str:
    """Returns digest of input message."""
    validate_message(message)
    raise Exception(r"Not implemented! ¯\_(ツ)_/¯")


def get_address(wif: str) -> str:
    """Returns the bitcoin address of the given input wif."""
    validate_wif(wif)
    return BTC.parse.wif(wif).address()


def sign(message: str, wif: str) -> str:
    """Returns signature of input message with provided wif."""
    validate_message(message)
    validate_wif(wif)
    key = BTC.parse.wif(wif)
    sig = BTC.msg.sign(key, message, verbose=0)
    return sig.encode('ascii')


def sign_digest(message_digest: str, wif: str) -> str:
    """Returns signature of input message digest with provided wif."""
    validate_digest(message_digest)
    validate_wif(wif)
    raise Exception(r"Not implemented! ¯\_(ツ)_/¯")


def verify(address: str, signature: str, message: str) -> str:
    """Verify signature if for given input message and address."""
    validate_address(address)
    validate_signature(signature)
    validate_message(message)
    return BTC.msg.verify(address, signature, message)


def verify_digest(address: str, signature: str, message_digest: str) -> str:
    """Verify signature if for given input message and address."""
    validate_address(address)
    validate_signature(signature)
    validate_digest(message_digest)
    raise Exception(r"Not implemented! ¯\_(ツ)_/¯")
