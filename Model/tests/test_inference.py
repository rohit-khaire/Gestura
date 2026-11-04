import numpy as np
import pytest
import torch

from inference import Detector, postprocess, preprocess
from model import DETR

CLASSES = ["a", "b"]


def outputs(logits, boxes):
    return {"pred_logits": torch.tensor([logits]), "pred_boxes": torch.tensor([boxes])}


def test_postprocess_drops_no_object_and_scales_boxes():
    out = outputs(
        logits=[[10.0, 0.0, 0.0],    # confident "a"
                [0.0, 0.0, 10.0],    # confident "no object" -> ignored
                [0.0, 10.0, 0.0]],   # confident "b"
        boxes=[[0.5, 0.5, 0.2, 0.2], [0.1, 0.1, 0.1, 0.1], [0.25, 0.75, 0.5, 0.5]],
    )
    dets = postprocess(out, CLASSES, width=200, height=100, threshold=0.9, max_detections=5)

    assert {d["label"] for d in dets} == {"a", "b"}
    a = next(d for d in dets if d["label"] == "a")
    assert a["class_id"] == 0
    assert a["bbox"] == pytest.approx([80, 40, 120, 60])
    b = next(d for d in dets if d["label"] == "b")
    assert b["bbox"] == pytest.approx([0, 50, 100, 99])  # y2 is clamped to height - 1


def test_postprocess_threshold_and_cap():
    out = outputs(
        logits=[[10.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.1, 0.0, 0.0]],  # last one is not confident
        boxes=[[0.5, 0.5, 0.2, 0.2]] * 3,
    )
    assert len(postprocess(out, CLASSES, 100, 100, threshold=0.9, max_detections=5)) == 2
    assert len(postprocess(out, CLASSES, 100, 100, threshold=0.9, max_detections=1)) == 1


def test_postprocess_nothing_found():
    out = outputs(logits=[[0.0, 0.0, 10.0]], boxes=[[0.5, 0.5, 0.2, 0.2]])
    assert postprocess(out, CLASSES, 100, 100, threshold=0.5, max_detections=5) == []


def test_preprocess_shape_and_channel_order():
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    frame[..., 2] = 255  # pure red in BGR
    x = preprocess(frame)
    assert x.shape == (1, 3, 224, 224)
    # after BGR->RGB the red channel (index 0) must be the bright one
    assert x[0, 0].mean() > x[0, 2].mean()


def test_detector_roundtrip(tmp_path):
    checkpoint = tmp_path / "model.pt"
    torch.save(DETR(num_classes=3, pretrained_backbone=False).state_dict(), checkpoint)

    detector = Detector(checkpoint, threshold=0.0, max_detections=5)  # threshold 0 keeps everything
    frame = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
    dets = detector(frame)

    assert len(dets) == 5
    for d in dets:
        x1, y1, x2, y2 = d["bbox"]
        assert 0 <= x1 <= x2 <= 159 and 0 <= y1 <= y2 <= 119
