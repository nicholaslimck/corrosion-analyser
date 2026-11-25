"""The paper record has to carry the inputs, because print hides the panel.

`@media print` sets `.offcanvas { display: none }`, and the panel is where the
inputs live - so the PDF used to reach the examiner as a verdict with no record
of the pipe it belonged to.
"""
from src.utils.assessment import assess
from src.utils.layout import build_print_summary
from src.utils.report import build_report
from tests.unittests.test_assessment import pipe_data


def report():
    return build_report(assess(pipe_data()))


def test_an_empty_report_renders_nothing():
    assert build_print_summary(None) == []
    assert build_print_summary({}) == []


def test_the_record_names_the_standard_and_the_pipe():
    text = str(build_print_summary(report()))
    assert 'DNVGL-RP-F101' in text
    assert '812.8 mm' in text
    assert '19.10 mm' in text


def test_the_record_carries_the_factors_and_the_verdict():
    text = str(build_print_summary(report()))
    assert 'Safety class' in text
    assert 'γm' in text
    assert 'Acceptable' in text


def test_the_record_lists_the_defect_geometry():
    rep = report()
    text = str(build_print_summary(rep))
    for defect in rep['defects']:
        assert f"{defect['length_mm']:.1f}" in text
        assert f"{defect['depth_mm']:.2f}" in text
