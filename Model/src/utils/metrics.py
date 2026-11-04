"""Object-detection metrics without heavy dependencies (plain Python, easy to unit-test).

Boxes are ``[x1, y1, x2, y2]``. A *sample* is one image: ``(ground_truths, detections)`` where
ground truths are ``{"class_id", "bbox"}`` and detections are ``{"class_id", "score", "bbox"}``.
"""

from __future__ import annotations


def iou_xyxy(a, b) -> float:
    """Intersection-over-union of two xyxy boxes."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def percentile(values, q: float) -> float:
    """Linear-interpolated percentile (q in 0-100). Returns 0.0 for an empty list."""
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def average_precision(scored_matches, n_gt: int):
    """All-point interpolated AP (PASCAL VOC 2010+). ``scored_matches`` is ``[(score, is_tp), ...]``.

    Returns ``None`` when the class has no ground truth (it is then left out of the mean).
    """
    if n_gt == 0:
        return None
    ranked = sorted(scored_matches, key=lambda m: -m[0])
    tp = fp = 0
    recalls, precisions = [0.0], [0.0]
    for _, is_tp in ranked:
        tp, fp = tp + is_tp, fp + (not is_tp)
        recalls.append(tp / n_gt)
        precisions.append(tp / (tp + fp))
    recalls.append(1.0)
    precisions.append(0.0)
    for i in range(len(precisions) - 2, -1, -1):  # make precision monotonically decreasing
        precisions[i] = max(precisions[i], precisions[i + 1])
    return sum((recalls[i] - recalls[i - 1]) * precisions[i] for i in range(1, len(recalls)))


def _class_matches(samples, class_id: int, iou_thr: float):
    """Greedy per-image matching of one class -> ([(score, is_tp)], number of ground truths)."""
    scored, n_gt = [], 0
    for gts, dets in samples:
        gt_boxes = [g["bbox"] for g in gts if g["class_id"] == class_id]
        n_gt += len(gt_boxes)
        used = [False] * len(gt_boxes)
        for det in sorted((d for d in dets if d["class_id"] == class_id), key=lambda d: -d["score"]):
            best, best_iou = -1, iou_thr
            for i, box in enumerate(gt_boxes):
                if used[i]:
                    continue
                overlap = iou_xyxy(det["bbox"], box)
                if overlap >= best_iou:
                    best, best_iou = i, overlap
            if best >= 0:
                used[best] = True
            scored.append((det["score"], best >= 0))
    return scored, n_gt


def confusion_matrix(samples, num_classes: int, iou_thr: float = 0.5, conf_thr: float = 0.5):
    """Object-level confusion matrix, size (C+1) x (C+1); index C is "background".

    ``cm[true][predicted]``: a detection matched to a ground-truth box (any class, IoU >= iou_thr)
    counts as that pair; an unmatched detection is ``cm[background][pred]`` (false positive) and an
    unmatched ground truth is ``cm[true][background]`` (missed sign).
    """
    bg = num_classes
    cm = [[0] * (num_classes + 1) for _ in range(num_classes + 1)]
    for gts, dets in samples:
        used = [False] * len(gts)
        for det in sorted((d for d in dets if d["score"] >= conf_thr), key=lambda d: -d["score"]):
            best, best_iou = -1, iou_thr
            for i, gt in enumerate(gts):
                if used[i]:
                    continue
                overlap = iou_xyxy(det["bbox"], gt["bbox"])
                if overlap >= best_iou:
                    best, best_iou = i, overlap
            if best >= 0:
                used[best] = True
                cm[gts[best]["class_id"]][det["class_id"]] += 1
            else:
                cm[bg][det["class_id"]] += 1
        for i, gt in enumerate(gts):
            if not used[i]:
                cm[gt["class_id"]][bg] += 1
    return cm


def evaluate_detections(samples, classes, iou_thr: float = 0.5, conf_thr: float = 0.5) -> dict:
    """AP / mAP (all detections) plus precision, recall and F1 at ``conf_thr`` for every class."""
    n = len(classes)
    cm = confusion_matrix(samples, n, iou_thr, conf_thr)

    per_class, aps = {}, []
    for c, name in enumerate(classes):
        scored, n_gt = _class_matches(samples, c, iou_thr)
        ap = average_precision(scored, n_gt)
        tp = cm[c][c]
        predicted = sum(cm[r][c] for r in range(n + 1))
        actual = sum(cm[c])
        precision = tp / predicted if predicted else 0.0
        recall = tp / actual if actual else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[name] = {"ap": ap, "precision": precision, "recall": recall, "f1": f1, "support": n_gt}
        if ap is not None:
            aps.append(ap)

    present = [m for m in per_class.values() if m["support"] > 0]
    mean = lambda key: sum(m[key] for m in present) / len(present) if present else 0.0  # noqa: E731
    return {
        "iou_threshold": iou_thr,
        "confidence_threshold": conf_thr,
        "images": len(samples),
        "map": sum(aps) / len(aps) if aps else 0.0,
        "macro_precision": mean("precision"),
        "macro_recall": mean("recall"),
        "macro_f1": mean("f1"),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classes": list(classes) + ["background"],
    }
