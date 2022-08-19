# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from guarantor import crypto
from guarantor import schemas
from guarantor import indexing


def test_index_update():
    doc_a = schemas.Identity(
        address="01234abcdef01",
        props={'name': "Alice", 'email': "alice@mail.com"},
    )

    doc_b = schemas.Identity(
        address="01234abcdef02",
        props={'name': "Bob", 'email': "bob@mail.com"},
    )
    bob_id = crypto.deterministic_json_hash(doc_b.dict())

    model_a_id = crypto.deterministic_json_hash(doc_a.dict())
    model_b_id = crypto.deterministic_json_hash(doc_b.dict())

    indexing.update_indexes(model_a_id, doc_a)
    indexing.update_indexes(model_b_id, doc_b)

    results = list(indexing.query_index("guarantor.schemas:Identity", search_term="bob"))
    assert len(results) == 2
    res0 = results[0]
    res1 = results[1]

    assert {res0.head , res1.head } == {bob_id}
    assert {res0.field, res1.field} == {"props.name", "props.email"}
    assert {res0.stem , res1.stem } == {"bob"       , "bob@mail.com"}
