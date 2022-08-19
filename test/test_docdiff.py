from guarantor import docdiff


def test_doc_diff():
    doc_v1_kw = {'title': "Hello, World!"}
    doc_v2_kw = {'title': "Hallo, Welt!"}
    diff_op   = docdiff.make_diff(doc_v1_kw, doc_v2_kw)
    assert docdiff.apply_diffs(doc_v1_kw, [diff_op]) == doc_v2_kw
