import logging
from pathlib import Path

import albumentations as A
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from utils.setup import get_classes

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
# Hue jitter used to be 0.5, which can rotate colours all the way round the wheel (blue skin...).
HUE_JITTER = 0.05
MAX_AUGMENT_ATTEMPTS = 50


def parse_label_file(path):
    """Read a YOLO-format label file: one ``class cx cy w h`` line per box (normalised 0-1).

    Returns ``(class_ids, boxes)`` as arrays of shape (N,) and (N, 4). Blank lines are ignored,
    and so is a missing trailing newline.
    """
    class_ids, boxes = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 5:
                raise ValueError(f"{path}: expected 'class cx cy w h', got {line.strip()!r}")
            class_ids.append(int(parts[0]))
            boxes.append([float(v) for v in parts[1:]])
    return np.array(class_ids, dtype=np.int64), np.array(boxes, dtype=np.float64).reshape(-1, 4)


def build_transforms(train: bool) -> A.Compose:
    steps = [A.Resize(500, 500)]
    if train:
        steps.append(A.RandomCrop(width=224, height=224, p=0.33))
    steps.append(A.Resize(224, 224))
    if train:
        steps += [
            A.HorizontalFlip(p=0.5),
            A.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5, hue=HUE_JITTER, p=0.5),
        ]
    steps += [A.Normalize(mean=MEAN, std=STD), A.ToTensorV2()]
    return A.Compose(steps, bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))


class DETRData(Dataset):
    """Images in ``<path>/images`` with YOLO labels in ``<path>/labels`` (same file stem)."""

    def __init__(self, path, train=True):
        super().__init__()
        self.path = Path(path)
        self.images_dir = self.path / 'images'
        self.labels_dir = self.path / 'labels'
        self.train = train
        self.label_files = sorted(
            p for p in self.labels_dir.iterdir() if p.suffix == '.txt' and p.name != 'classes.txt'
        )

        self.transform = build_transforms(train)
        # Training crops/flips can push every box out of the image. In that case we fall back to
        # the plain resize + normalise pipeline (never the raw, un-normalised image).
        self.fallback_transform = build_transforms(False) if train else self.transform

        logger.info("%s set: %d samples in %s", "Train" if train else "Test", len(self), self.path)

    def __len__(self):
        return len(self.label_files)

    def _find_image(self, stem: str) -> Path:
        for ext in IMAGE_EXTENSIONS:
            candidate = self.images_dir / f'{stem}{ext}'
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f'No image named {stem}{{{",".join(IMAGE_EXTENSIONS)}}} in {self.images_dir}')

    def _augment(self, image, boxes, class_ids):
        attempts = MAX_AUGMENT_ATTEMPTS if self.train else 1
        for _ in range(attempts):
            try:
                out = self.transform(image=image, bboxes=boxes, class_labels=class_ids)
            except ValueError:  # e.g. a box that ended up outside the image after cropping
                continue
            if len(out['bboxes']) > 0:
                return out
        return self.fallback_transform(image=image, bboxes=boxes, class_labels=class_ids)

    def __getitem__(self, idx):
        label_path = self.label_files[idx]
        image = np.array(Image.open(self._find_image(label_path.stem)).convert('RGB'))
        class_ids, boxes = parse_label_file(label_path)

        out = self._augment(image, boxes, class_ids)

        labels = torch.as_tensor(np.asarray(out['class_labels']), dtype=torch.long)
        boxes = torch.as_tensor(np.asarray(out['bboxes'], dtype=np.float32).reshape(-1, 4))
        return out['image'], {'labels': labels, 'boxes': boxes}


if __name__ == '__main__':
    # Quick look at a few augmented training samples: python src/data.py data/train
    import sys

    from matplotlib import pyplot as plt

    from utils.boxes import rescale_bboxes

    classes = get_classes()
    dataset = DETRData(sys.argv[1] if len(sys.argv) > 1 else 'data/train', train=True)
    fig, axes = plt.subplots(2, 2)
    for i, ax in enumerate(axes.flatten()):
        img, target = dataset[i % len(dataset)]
        # undo the ImageNet normalisation just for display
        shown = (img.permute(1, 2, 0) * torch.tensor(STD) + torch.tensor(MEAN)).clamp(0, 1)
        ax.imshow(shown)
        for cls, (x1, y1, x2, y2) in zip(target['labels'], rescale_bboxes(target['boxes'], (224, 224))):
            ax.add_patch(plt.Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, color='tab:blue', linewidth=3))
            ax.text(x1, y1, classes[int(cls)], fontsize=12, bbox=dict(facecolor='yellow', alpha=0.5))
    fig.tight_layout()
    plt.show()
