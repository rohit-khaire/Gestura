import pytest
import torch

from utils.boxes import (
    box_cxcywh_to_xyxy,
    box_xyxy_to_cxcywh,
    generalized_box_iou,
    rescale_bboxes,
    stacker,
)


def test_box_format_roundtrip():
    boxes = torch.tensor([[0.5, 0.5, 0.2, 0.4], [0.3, 0.7, 0.1, 0.1]])
    assert torch.allclose(box_xyxy_to_cxcywh(box_cxcywh_to_xyxy(boxes)), boxes, atol=1e-6)


def test_rescale_bboxes_uses_width_then_height():
    out = rescale_bboxes(torch.tensor([[0.5, 0.5, 0.5, 0.5]]), (200, 100))
    assert out.tolist() == [[50.0, 25.0, 150.0, 75.0]]


def test_giou_identical_boxes_is_one():
    b = torch.tensor([[0.1, 0.1, 0.5, 0.5]])
    assert generalized_box_iou(b, b).item() == pytest.approx(1.0, abs=1e-5)


def test_giou_disjoint_boxes_is_negative():
    a = torch.tensor([[0.0, 0.0, 0.2, 0.2]])
    b = torch.tensor([[0.8, 0.8, 1.0, 1.0]])
    assert generalized_box_iou(a, b).item() < 0


def test_stacker_keeps_targets_as_list():
    batch = [(torch.zeros(3, 4, 4), {"labels": torch.tensor([1])}),
             (torch.zeros(3, 4, 4), {"labels": torch.tensor([0, 2])})]
    images, targets = stacker(batch)
    assert images.shape == (2, 3, 4, 4)
    assert len(targets) == 2 and len(targets[1]["labels"]) == 2
