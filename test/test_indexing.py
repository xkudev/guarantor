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

    model_a_id: Hash = crypto.deterministic_json_hash(model_a.dict())
    model_b_id: Hash = crypto.deterministic_json_hash(model_b.dict())

    indexing.update_indexes(model_a_id, model_a)
    indexing.update_indexes(model_b_id, model_b)

    results = list(indexing.query_index(schemas.Identity, search_term="bob"))
    assert len(results) == 2
    res0 = results[0]
    res1 = results[1]

    assert {res0.model_id, res1.model_id} == {bob_hash}
    assert {res0.field   , res1.field     } == {"props.name", "props.email"}
    assert {res0.stem    , res1.stem      } == {"bob"       , "bob@mail.com"}
