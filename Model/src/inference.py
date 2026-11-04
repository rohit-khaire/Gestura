"""Inference code shared by the API, the webcam demo and the test script.

Before this module existed each of them had its own copy of the pre/post-processing, and they
disagreed (the webcam demo fed BGR frames to a model trained on RGB, and hard-coded a
1920x1080 frame size for the boxes).
"""

from pathlib import Path

import cv2
import numpy as np
import torch

from model import DETR
from utils.setup import get_classes, get_colors

INPUT_SIZE = 224
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess(frame_bgr: np.ndarray) -> torch.Tensor:
    """BGR uint8 frame (H, W, 3) -> normalised RGB tensor (1, 3, 224, 224)."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_LINEAR)
    x = (rgb.astype(np.float32) / 255.0 - MEAN) / STD
    return torch.from_numpy(x).permute(2, 0, 1).unsqueeze(0).contiguous()


def postprocess(outputs: dict, classes: list, width: int, height: int,
                threshold: float, max_detections: int) -> list:
    """Turn raw DETR outputs for ONE image into a list of detections.

    Each detection is ``{"class_id", "label", "score", "bbox": [x1, y1, x2, y2]}`` with the box
    in pixel coordinates of the original ``width`` x ``height`` frame. Detections are sorted by
    score and capped at ``max_detections``.
    """
    probs = outputs["pred_logits"][0].softmax(-1)[:, :-1]  # drop the "no object" column
    scores, labels = probs.max(-1)

    keep = (scores >= threshold).nonzero(as_tuple=True)[0]
    if keep.numel() == 0:
        return []
    keep = keep[scores[keep].argsort(descending=True)][:max_detections]

    cx, cy, w, h = outputs["pred_boxes"][0][keep].unbind(-1)
    x1 = ((cx - w / 2) * width).clamp(0, width - 1)
    y1 = ((cy - h / 2) * height).clamp(0, height - 1)
    x2 = ((cx + w / 2) * width).clamp(0, width - 1)
    y2 = ((cy + h / 2) * height).clamp(0, height - 1)

    detections = []
    for i, query in enumerate(keep.tolist()):
        class_id = int(labels[query])
        detections.append({
            "class_id": class_id,
            "label": classes[class_id],
            "score": float(scores[query]),
            "bbox": [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])],
        })
    return detections


class Detector:
    """Loads a checkpoint once and runs detection on BGR frames (as read by OpenCV)."""

    def __init__(self, checkpoint, threshold: float = 0.9, max_detections: int = 5, device=None):
        self.classes = get_classes()
        self.threshold = threshold
        self.max_detections = max_detections
        self.device = torch.device(device) if device else torch.device("cpu")

        self.model = DETR(num_classes=len(self.classes), pretrained_backbone=False)
        self.model.load_pretrained(Path(checkpoint))
        self.model.eval().to(self.device)

    @torch.inference_mode()
    def __call__(self, frame_bgr: np.ndarray) -> list:
        height, width = frame_bgr.shape[:2]
        outputs = self.model(preprocess(frame_bgr).to(self.device))
        outputs = {k: v.cpu() for k, v in outputs.items()}
        return postprocess(outputs, self.classes, width, height,
                           self.threshold, self.max_detections)


def draw_detections(frame: np.ndarray, detections: list) -> np.ndarray:
    """Draw boxes + labels onto a BGR frame in place and return it."""
    colors = get_colors()
    for det in detections:
        x1, y1, x2, y2 = (int(v) for v in det["bbox"])
        rgb = colors[det["class_id"] % len(colors)]
        bgr = (rgb[2], rgb[1], rgb[0])  # config.json stores RGB, OpenCV wants BGR
        cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)

        text = f"{det['label']} {det['score']:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        top = max(y1, th + 6)  # keep the label inside the frame
        cv2.rectangle(frame, (x1, top - th - 6), (x1 + tw, top), bgr, -1)
        cv2.putText(frame, text, (x1, top - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2, cv2.LINE_AA)
    return frame
