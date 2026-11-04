import numpy as np
import pytest
from PIL import Image

from data import DETRData, parse_label_file
from utils.boxes import stacker


def make_split(root, n=3):
    (root / "images").mkdir(parents=True)
    (root / "labels").mkdir()
    for i in range(n):
        pixels = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
        Image.fromarray(pixels).save(root / "images" / f"img{i}.jpg")
        # No trailing newline on purpose: this used to crash the loader.
        (root / "labels" / f"img{i}.txt").write_text("1 0.5 0.5 0.4 0.4")
    return root


def test_parse_label_file_handles_blank_lines_and_no_trailing_newline(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.2 0.2\n\n2 0.1 0.2 0.3 0.4")
    class_ids, boxes = parse_label_file(f)
    assert class_ids.tolist() == [0, 2]
    assert boxes.shape == (2, 4)


def test_parse_label_file_rejects_malformed_lines(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_text("0 0.5 0.5")
    with pytest.raises(ValueError):
        parse_label_file(f)


@pytest.mark.parametrize("train", [False, True])
def test_dataset_items_are_normalised_tensors(tmp_path, train):
    ds = DETRData(make_split(tmp_path / "split"), train=train)
    assert len(ds) == 3
    image, target = ds[0]
    assert image.shape == (3, 224, 224)
    assert target["labels"].tolist() == [1]
    assert target["boxes"].shape == (1, 4)


def test_dataset_batches_with_stacker(tmp_path):
    ds = DETRData(make_split(tmp_path / "split"), train=True)
    images, targets = stacker([ds[0], ds[1]])
    assert images.shape == (2, 3, 224, 224)
    assert len(targets) == 2
