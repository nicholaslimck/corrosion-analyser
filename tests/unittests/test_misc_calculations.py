from core.calculations.misc_calculations import calculate_std_dev


def test_calculate_std_dev(snapshot):
    acc_rel = 0.1
    conf = 0.8
    assert calculate_std_dev(acc_rel, conf) == snapshot
