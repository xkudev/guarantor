# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from guarantor import schemas
from guarantor import indexing


def test_index_update():
    model_a = schemas.Identity(
        address="01234abcdef01",
        props={'name': "Alice", 'email': "alice@mail.com"},
    )

    model_b = schemas.Identity(
        address="01234abcdef02",
        props={'name': "Bob", 'email': "bob@mail.com"},
    )

    indexing.update_indexes(model_a)
    indexing.update_indexes(model_b)

    res = indexing.query_index("01234abcdef")
    print(res)
    assert False
