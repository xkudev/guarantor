from pycoin.symbols.btc import network as BTC

ADDRESS = "bc1qt3y9cxcw93w9h4u0n9sm30p6n4sn4t88hx2rxu"
PUBLIC_KEYS = "03eaa795767400e53e8b63685b41dd512eb7de7fd5d7a51f5657003685a43bd92d"
PRIVATE_KEY = "p2wpkh:L23nLNHmLoCkK1biBmY7z3tdY8qXJAkcerNP3SoxoTVHDgC5FzDr"
MESSAGE = "TEST_MESSAGE"
SIGNATURE = (
    "HxVrktEEv/3tLOUJ19HijkkAFvlzUV6rh5HFKfyyiPnPVcoBCrqivZBOGNffIoeds5nWBCQOXMY6C03qXQiYJZI="
)
ENCRYPTED = (
    "QklFMQJvsEjHP/ZXsK1yeZt2pMl3JV0Kmo/oZpHbD/68eMF5jHjUz7Twgq"
    "Ps0O3GyolvhZPAGfTK39N0Xi0eP4C4XFWOpUFUCduhc63p36g4sXbHDw=="
)


def test_against_myself():
    """
    Test code that verifies against ourselves only. Useful but not so great.
    """

    for wif, right_addr in [
        (
            'L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp',
            '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv',
        ),
        (
            '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
            '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN',
        ),
    ]:
        key = BTC.parse.wif(wif)
        assert key.address() == right_addr

        vk2 = BTC.parse.address(right_addr)
        assert vk2.address() == right_addr

        for i in range(1, 30, 10):
            msg = f"test message {'A' * i}"
            sig = BTC.msg.sign(key, msg, verbose=1)
            assert right_addr in sig

            # check parsing works
            parsed_msg, parsed_addr, parsed_sig = BTC.msg.parse_signed(sig)
            assert parsed_msg == msg, parsed_msg
            assert parsed_addr == right_addr, parsed_addr

            sig2 = BTC.msg.sign(key, msg, verbose=0)
            assert sig2 in sig, (sig, sig2)

            assert parsed_sig == sig2, parsed_sig

            assert BTC.msg.verify(key, sig2, msg)

            assert BTC.msg.verify(key, sig2.encode('ascii'), msg)
