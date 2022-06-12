from pycoin.symbols.btc import network as BTC


def sign(message, wif):
    key = BTC.parse.wif(wif)
    sig = BTC.msg.sign(key, message, verbose=0)
    return sig.encode('ascii')
