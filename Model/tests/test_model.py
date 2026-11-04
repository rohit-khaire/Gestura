import pytest
import torch

from model import DETR


def test_forward_shapes():
    model = DETR(num_classes=3, pretrained_backbone=False).eval()
    with torch.no_grad():
        out = model(torch.randn(2, 3, 224, 224))
    assert out["pred_logits"].shape == (2, 25, 4)  # 3 classes + "no object"
    assert out["pred_boxes"].shape == (2, 25, 4)
    assert out["pred_boxes"].min() >= 0 and out["pred_boxes"].max() <= 1


def test_load_pretrained_roundtrip(tmp_path):
    source = DETR(num_classes=3, pretrained_backbone=False)
    torch.save(source.state_dict(), tmp_path / "m.pt")

    target = DETR(num_classes=3, pretrained_backbone=False).load_pretrained(tmp_path / "m.pt")
    assert torch.equal(source.linear_class.weight, target.linear_class.weight)


def test_load_pretrained_fails_loudly(tmp_path):
    model = DETR(num_classes=3, pretrained_backbone=False)
    with pytest.raises(FileNotFoundError):
        model.load_pretrained(tmp_path / "missing.pt")

    torch.save(DETR(num_classes=2, pretrained_backbone=False).state_dict(), tmp_path / "wrong.pt")
    with pytest.raises(RuntimeError):  # wrong number of classes
        model.load_pretrained(tmp_path / "wrong.pt")


def test_expand_head_keeps_old_classes_and_no_object(tmp_path):
    old = DETR(num_classes=3, pretrained_backbone=False)
    torch.save(old.state_dict(), tmp_path / "old.pt")

    new = DETR(num_classes=5, pretrained_backbone=False).load_pretrained(tmp_path / "old.pt", expand_head=True)

    assert new.linear_class.weight.shape == (6, 256)
    assert torch.equal(new.linear_class.weight[:3], old.linear_class.weight[:3])  # old signs kept
    assert torch.equal(new.linear_class.weight[-1], old.linear_class.weight[-1])  # "no object" kept
    assert torch.equal(new.linear_class.bias[:3], old.linear_class.bias[:3])
    assert torch.equal(new.conv.weight, old.conv.weight)  # the rest of the network is identical


def test_expand_head_is_opt_in_and_never_shrinks(tmp_path):
    torch.save(DETR(num_classes=3, pretrained_backbone=False).state_dict(), tmp_path / "old.pt")
    with pytest.raises(RuntimeError):  # default stays strict
        DETR(num_classes=5, pretrained_backbone=False).load_pretrained(tmp_path / "old.pt")

    torch.save(DETR(num_classes=5, pretrained_backbone=False).state_dict(), tmp_path / "big.pt")
    with pytest.raises(ValueError):
        DETR(num_classes=3, pretrained_backbone=False).load_pretrained(tmp_path / "big.pt", expand_head=True)
