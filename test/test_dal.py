# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
from guarantor import schemas
from guarantor.dal import DataAccessLayer

from . import fixtures


def test_basic(tmpdir):
    dal = DataAccessLayer(wif=fixtures.KEYS_FIXTURES[0].wif, db_dir=tmpdir)

    doc_wrp_v1 = dal.new(schemas.GenericDocument, title="Hello, World!", props={})
    doc_wrp_v2 = doc_wrp_v1.update(title="Hallo, Welt!").save()

    assert doc_wrp_v1 == dal.get(head=doc_wrp_v1.head)
    assert doc_wrp_v2 == dal.get(head=doc_wrp_v2.head)

    # make sure they're newly constricted
    assert id(doc_wrp_v1) != id(dal.get(head=doc_wrp_v1.head))
    assert id(doc_wrp_v2) != id(dal.get(head=doc_wrp_v2.head))


def test_search(tmpdir):
    dal = DataAccessLayer(wif=fixtures.KEYS_FIXTURES[0].wif, db_dir=tmpdir)

    doc_wrp_a = dal.new(schemas.GenericDocument, title="Hello, World!" , props={})
    doc_wrp_b = dal.new(schemas.GenericDocument, title="Dummy Document", props={})

    doc_wrp = dal.find_one("guarantor.schemas:GenericDocument", title="World")
    assert doc_wrp is None

    doc_wrp_a = doc_wrp_a.save()
    doc_wrp_b = doc_wrp_b.save()

    assert doc_wrp_a == dal.find_one("guarantor.schemas:GenericDocument", title="hello")
    assert doc_wrp_a == dal.find_one("guarantor.schemas:GenericDocument", title="World")
