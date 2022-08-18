from guarantor import dht


def test_change():

    wif = "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss"
    expected_address = "1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN"

    change = dht.create_change(wif, 0, "foo")
    dht.validate_change(change)

    assert change.address == expected_address

    change_hash = dht.get_change_hash(change)
