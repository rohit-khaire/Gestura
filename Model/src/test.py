"""Visual check: run the detector on random test images and show the result.

    python src/test.py --checkpoint pretrained/4426_model.pt --count 4
"""

import argparse
import random
import time
from pathlib import Path

import cv2
from matplotlib import pyplot as plt

from data import IMAGE_EXTENSIONS
from inference import Detector, draw_detections


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--checkpoint', default='pretrained/4426_model.pt')
    p.add_argument('--data', default='data/test/images', help='folder of test images')
    p.add_argument('--count', type=int, default=4, help='how many random images to show')
    p.add_argument('--threshold', type=float, default=0.95)
    p.add_argument('--save', default=None, help='save the figure to this path instead of opening a window')
    args = p.parse_args()

    images = sorted(f for f in Path(args.data).iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
    if not images:
        raise SystemExit(f'No images found in {args.data}')
    sample = random.sample(images, min(args.count, len(images)))

    detector = Detector(args.checkpoint, threshold=args.threshold)

    cols = 2 if len(sample) > 1 else 1
    rows = (len(sample) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, squeeze=False)
    for ax in axes.flat:
        ax.axis('off')

    for ax, path in zip(axes.flat, sample):
        frame = cv2.imread(str(path))
        start = time.perf_counter()
        detections = detector(frame)
        ms = (time.perf_counter() - start) * 1000
        print(f'{path.name}: {len(detections)} detection(s) in {ms:.0f} ms')
        for d in detections:
            print(f"    {d['label']} {d['score']:.2f} {[round(v) for v in d['bbox']]}")
        ax.imshow(cv2.cvtColor(draw_detections(frame, detections), cv2.COLOR_BGR2RGB))
        ax.set_title(path.name, fontsize=8)

    fig.tight_layout()
    if args.save:
        fig.savefig(args.save, dpi=150)
    else:
        plt.show()


if __name__ == '__main__':
    main()
