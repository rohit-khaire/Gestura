import pytest

from utils.metrics import average_precision, confusion_matrix, evaluate_detections, iou_xyxy, percentile

BOX = [0, 0, 100, 100]


def gt(c, box=BOX):
    return {"class_id": c, "bbox": box}


def det(c, score, box=BOX):
    return {"class_id": c, "score": score, "bbox": box}


def test_iou_identical_disjoint_and_half_overlap():
    assert iou_xyxy(BOX, BOX) == pytest.approx(1.0)
    assert iou_xyxy(BOX, [200, 200, 300, 300]) == 0.0
    assert iou_xyxy([0, 0, 10, 10], [5, 0, 15, 10]) == pytest.approx(50 / 150)


def test_percentile():
    assert percentile([], 50) == 0.0
    assert percentile([10], 95) == 10
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([0, 10], 95) == pytest.approx(9.5)


def test_average_precision_perfect_and_empty():
    assert average_precision([(0.9, True), (0.8, True)], 2) == pytest.approx(1.0)
    assert average_precision([(0.9, False)], 2) == pytest.approx(0.0)
    assert average_precision([(0.9, True)], 0) is None


def test_average_precision_penalises_a_false_positive_ranked_first():
    # ranking: FP, TP -> precision at the single recall step is 1/2
    assert average_precision([(0.9, False), (0.8, True)], 1) == pytest.approx(0.5)


def test_perfect_detector():
    samples = [([gt(0), gt(1, [200, 0, 300, 100])], [det(0, 0.9), det(1, 0.8, [200, 0, 300, 100])])]
    r = evaluate_detections(samples, ["a", "b"])
    assert r["map"] == pytest.approx(1.0)
    assert r["macro_f1"] == pytest.approx(1.0)
    assert r["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 0]]


def test_wrong_class_counts_as_confusion_not_a_hit():
    samples = [([gt(0)], [det(1, 0.9)])]
    cm = confusion_matrix(samples, 2)
    assert cm[0][1] == 1  # true class 0 predicted as 1
    r = evaluate_detections(samples, ["a", "b"])
    assert r["per_class"]["a"]["recall"] == 0.0
    assert r["per_class"]["b"]["precision"] == 0.0


def test_missed_sign_and_false_alarm():
    samples = [([gt(0)], []), ([], [det(0, 0.9)])]
    cm = confusion_matrix(samples, 1)
    assert cm == [[0, 1], [1, 0]]  # [class0->bg] missed, [bg->class0] false alarm
    r = evaluate_detections(samples, ["a"])
    assert r["per_class"]["a"]["precision"] == 0.0
    assert r["per_class"]["a"]["recall"] == 0.0


def test_low_confidence_detections_are_ignored_for_precision_but_not_for_ap():
    samples = [([gt(0)], [det(0, 0.2)])]
    r = evaluate_detections(samples, ["a"], conf_thr=0.5)
    assert r["per_class"]["a"]["recall"] == 0.0
    assert r["per_class"]["a"]["ap"] == pytest.approx(1.0)


def test_poorly_placed_box_is_not_a_match():
    samples = [([gt(0)], [det(0, 0.9, [60, 60, 160, 160])])]  # IoU ~ 0.12
    r = evaluate_detections(samples, ["a"])
    assert r["map"] == pytest.approx(0.0)


def test_class_without_ground_truth_is_left_out_of_the_mean():
    samples = [([gt(0)], [det(0, 0.9)])]
    r = evaluate_detections(samples, ["a", "never_seen"])
    assert r["per_class"]["never_seen"]["ap"] is None
    assert r["map"] == pytest.approx(1.0)
