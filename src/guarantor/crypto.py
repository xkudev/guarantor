from pycoin.symbols.btc import network as BTC


def sign(message, wif):
    key = BTC.parse.wif(wif)
    sig = BTC.msg.sign(key, message, verbose=0)
    return sig.encode('ascii')


def wif_address(wif):
    return BTC.parse.wif(wif).address()


def verify(address, signature, message):
    return BTC.msg.verify(address, signature, message)
