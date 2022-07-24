# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from guarantor import crypto
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
    bob_hash = crypto.deterministic_json_hash(model_b.dict())

    indexing.update_indexes(model_a)
    indexing.update_indexes(model_b)

    results = list(indexing.query_index(schemas.Identity, search_term="bob"))
    assert len(results) == 2
    res0 = results[0]
    assert res0.model_hash == bob_hash
    assert res0.field      == "props.email"
    assert res0.stem       == "bob@mail.com"

    res1 = results[1]
    assert res1.model_hash == bob_hash
    assert res1.field      == "props.name"
    assert res1.stem       == "bob"
