"""Measure the detector on the test set and write the numbers the README asks for.

    python src/evaluate.py --checkpoint pretrained/4426_model.pt --data data/test

Writes ``results/metrics.json``, ``results/metrics.md`` (paste it into the README) and, if
matplotlib is installed, ``results/confusion_matrix.png``.

Reported: mAP@IoU, per-class AP / precision / recall / F1, a confusion matrix and the inference
latency (median and 95th percentile, on this machine's CPU unless you pass --device).
"""

import argparse
import json
import time
from pathlib import Path

import cv2

from data import IMAGE_EXTENSIONS, parse_label_file
from inference import Detector
from utils.metrics import evaluate_detections, percentile
from utils.setup import get_classes


def load_samples(detector, data_dir: Path):
    """Run the detector over every labelled image -> (samples, latencies in ms)."""
    images_dir, labels_dir = data_dir / "images", data_dir / "labels"
    label_files = sorted(p for p in labels_dir.glob("*.txt") if p.name != "classes.txt")
    if not label_files:
        raise SystemExit(f"No label files found in {labels_dir}")

    samples, latencies = [], []
    for label_file in label_files:
        image_path = next(
            (images_dir / f"{label_file.stem}{ext}" for ext in IMAGE_EXTENSIONS
             if (images_dir / f"{label_file.stem}{ext}").exists()),
            None,
        )
        if image_path is None:
            print(f"skipping {label_file.name}: no matching image")
            continue
        frame = cv2.imread(str(image_path))
        height, width = frame.shape[:2]

        class_ids, boxes = parse_label_file(label_file)  # YOLO: cx, cy, w, h (0-1)
        gts = [
            {
                "class_id": int(c),
                "bbox": [(cx - w / 2) * width, (cy - h / 2) * height,
                         (cx + w / 2) * width, (cy + h / 2) * height],
            }
            for c, (cx, cy, w, h) in zip(class_ids, boxes)
        ]

        start = time.perf_counter()
        detections = detector(frame)
        latencies.append((time.perf_counter() - start) * 1000)
        samples.append((gts, detections))
    return samples, latencies


def to_markdown(result: dict, latencies, checkpoint) -> str:
    rows = ["| Sign | AP | Precision | Recall | F1 | Test boxes |", "| --- | --- | --- | --- | --- | --- |"]
    for name, m in result["per_class"].items():
        ap = "n/a" if m["ap"] is None else f"{m['ap']:.3f}"
        rows.append(f"| {name} | {ap} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['support']} |")
    return "\n".join([
        f"**Checkpoint:** `{checkpoint}` · **Test images:** {result['images']} · "
        f"**IoU:** {result['iou_threshold']} · **Confidence threshold:** {result['confidence_threshold']}",
        "",
        f"**mAP@{result['iou_threshold']}: {result['map']:.3f}** · macro precision {result['macro_precision']:.3f} · "
        f"macro recall {result['macro_recall']:.3f} · macro F1 {result['macro_f1']:.3f}",
        "",
        *rows,
        "",
        f"Inference latency (CPU): median {percentile(latencies, 50):.0f} ms, p95 {percentile(latencies, 95):.0f} ms per frame.",
        "",
    ])


def save_confusion_plot(result: dict, path: Path) -> None:
    try:
        from matplotlib import pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipping the confusion-matrix image")
        return
    cm, names = result["confusion_matrix"], result["classes"]
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(names)), names, rotation=45, ha="right")
    ax.set_yticks(range(len(names)), names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    for i, row in enumerate(cm):
        for j, value in enumerate(row):
            ax.text(j, i, value, ha="center", va="center", color="black" if value < max(map(max, cm)) / 2 else "white")
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--checkpoint", default="pretrained/4426_model.pt")
    p.add_argument("--data", default="data/test", help="folder with images/ and labels/ (YOLO format)")
    p.add_argument("--iou", type=float, default=0.5, help="IoU needed for a detection to count as correct")
    p.add_argument("--conf", type=float, default=0.5, help="confidence cut-off for precision/recall/confusion")
    p.add_argument("--device", default=None, help="e.g. cuda; default is CPU")
    p.add_argument("--out", default="results")
    args = p.parse_args()

    # Low threshold + many queries so the AP curve sees the whole ranking.
    detector = Detector(args.checkpoint, threshold=0.05, max_detections=25, device=args.device)
    samples, latencies = load_samples(detector, Path(args.data))
    result = evaluate_detections(samples, get_classes(), iou_thr=args.iou, conf_thr=args.conf)
    result["latency_ms"] = {"median": percentile(latencies, 50), "p95": percentile(latencies, 95)}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=2))
    markdown = to_markdown(result, latencies, args.checkpoint)
    (out / "metrics.md").write_text(markdown)
    save_confusion_plot(result, out / "confusion_matrix.png")
    print(markdown)
    print(f"Saved to {out}/")


if __name__ == "__main__":
    main()
