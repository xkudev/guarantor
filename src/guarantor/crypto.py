from pycoin.symbols.btc import network as BTC


def validate_address(address: str):
    """Raises ValueError if given address not valid."""
    if not BTC.parse.p2pkh(address):
        raise ValueError(f"Invalid BTC address: {address}")


def validate_wif(wif: str):
    """Raises ValueError if given input cannot be used for signing."""
    if not BTC.parse.wif(wif):
        raise ValueError(f"Invalid WIF: {wif}")


def get_address(wif: str) -> str:
    """Returns the bitcoin address of the given input wif."""
    validate_wif(wif)
    return str(BTC.parse.wif(wif).address())


def sign(message: str, wif: str) -> str:
    """Returns signature of input message with provided wif."""
    validate_wif(wif)
    key = BTC.parse.wif(wif)
    return str(BTC.msg.sign(key, message, verbose=0))


def verify(address: str, signature: str, message: str) -> str:
    """Verify signature if for given input message and address."""
    validate_address(address)
    return str(BTC.msg.verify(address, signature, message))
