import torch

from loss import DETRLoss, HungarianMatcher

WEIGHTS = {"class_weighting": 1, "bbox_weighting": 5, "giou_weighting": 2}


def make_criterion(num_classes=3):
    return DETRLoss(num_classes, HungarianMatcher(WEIGHTS), WEIGHTS, eos_coef=0.1)


def test_loss_is_finite_and_backpropagates():
    outputs = {
        "pred_logits": torch.randn(2, 10, 4, requires_grad=True),
        "pred_boxes": torch.rand(2, 10, 4, requires_grad=True),
    }
    targets = [
        {"labels": torch.tensor([1, 2]), "boxes": torch.tensor([[0.5, 0.5, 0.2, 0.3], [0.3, 0.7, 0.1, 0.2]])},
        {"labels": torch.tensor([0]), "boxes": torch.tensor([[0.4, 0.6, 0.3, 0.4]])},
    ]
    criterion = make_criterion()
    total = criterion.total_loss(criterion(outputs, targets))

    assert torch.isfinite(total)
    total.backward()
    assert outputs["pred_boxes"].grad is not None


def test_perfect_box_prediction_has_near_zero_box_loss():
    target_box = torch.tensor([0.5, 0.5, 0.3, 0.3])
    boxes = torch.tensor([[[0.9, 0.9, 0.05, 0.05]] * 5])
    boxes[0, 2] = target_box
    logits = torch.zeros(1, 5, 4)
    logits[0, 2, 1] = 20.0  # query 2 confidently predicts class 1

    outputs = {"pred_logits": logits, "pred_boxes": boxes}
    targets = [{"labels": torch.tensor([1]), "boxes": target_box.unsqueeze(0)}]
    losses = make_criterion()(outputs, targets)

    assert losses["boxes"]["loss_bbox"].item() < 1e-4
    assert losses["boxes"]["loss_giou"].item() < 1e-4
