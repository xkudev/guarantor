import typing as typ
import hashlib

import jcs
from pycoin.symbols.btc import network as BTC


def validate_address(address: str):
    """Raises ValueError if given address not valid."""
    if not BTC.parse.p2pkh(address):
        raise ValueError(f"Invalid BTC address: {address}")


def validate_wif(wif: str):
    """Raises ValueError if given input cannot be used for signing."""
    if not BTC.parse.wif(wif):
        raise ValueError(f"Invalid WIF: {wif}")


def get_wif_address(wif: str) -> str:
    """Returns the bitcoin address of the given input wif."""
    validate_wif(wif)
    return str(BTC.parse.wif(wif).address())


def get_pubkey_address(wif: str) -> str:
    raise Exception("Please implement")


def get_pubkey(wif: str) -> str:
    raise Exception("Please implement")


def sign(message: str, wif: str) -> str:
    """Returns signature of input message with provided wif."""
    validate_wif(wif)
    key = BTC.parse.wif(wif)
    return str(BTC.msg.sign(key, message, verbose=0))


def verify(address: str, signature: str, message: str) -> bool:
    """Verify signature if for given input message and address."""
    validate_address(address)
    return bool(BTC.msg.verify(address, signature, message))


def deterministic_json_hash(obj: typ.Any) -> str:
    """Returns sha256 hex digest of object serialized according to RFC 8785"""
    sha256 = hashlib.sha256()
    sha256.update(jcs.canonicalize(obj))
    return sha256.hexdigest()
