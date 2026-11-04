"""Capture training images from a webcam, one burst per class from config.json.

    python src/utils/collect_images.py --out data/raw --per-class 30
    python src/utils/collect_images.py --only stop yes good --per-class 150   # just some classes

For each class a live preview opens; press SPACE to start the burst, ``q`` to quit.
Label the saved images afterwards (e.g. with Label Studio, YOLO export).
Needs a GUI build of OpenCV (``pip install opencv-python``), not ``opencv-python-headless``.
"""

import argparse
import sys
import time
import uuid
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make `utils` importable when run as a script
from utils.setup import get_classes  # noqa: E402

WINDOW = 'Image capture'


def show(frame, text):
    preview = frame.copy()
    cv2.putText(preview, text, (10, 40), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(preview, text, (10, 40), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow(WINDOW, preview)
    return cv2.waitKey(1) & 0xFF


def read(cap):
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError('Failed to read from the camera')
    return frame


def wait_for_space(cap, class_name):
    """Live preview until SPACE (returns True) or q (returns False)."""
    while True:
        key = show(read(cap), f'Next: {class_name} - press SPACE')
        if key == ord(' '):
            return True
        if key == ord('q'):
            return False


def capture_class(cap, out_dir, class_name, count, delay):
    """Save ``count`` frames, ``delay`` seconds apart. Returns False if the user pressed q."""
    saved, next_shot = 0, time.time()
    while saved < count:
        frame = read(cap)
        if time.time() >= next_shot:
            cv2.imwrite(str(out_dir / f'{class_name}-{uuid.uuid4().hex[:12]}.jpg'), frame)
            saved += 1
            next_shot = time.time() + delay
        if show(frame, f'{class_name}: {saved}/{count}') == ord('q'):
            return False
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', default='data/raw', help='output folder')
    p.add_argument('--camera', type=int, default=0)
    p.add_argument('--per-class', type=int, default=30, help='images to capture per class')
    p.add_argument('--delay', type=float, default=1.0, help='seconds between shots')
    p.add_argument('--only', nargs='+', default=None, metavar='CLASS',
                   help='capture just these classes (e.g. the new signs) instead of all of config.json')
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f'Could not open camera {args.camera}')

    try:
        classes = get_classes()
        if args.only:
            unknown = [name for name in args.only if name not in classes]
            if unknown:
                raise SystemExit(f'Not in config.json: {unknown}. Known classes: {classes}')
            classes = args.only
        for class_name in classes:
            if not wait_for_space(cap, class_name):
                break
            if not capture_class(cap, out_dir, class_name, args.per_class, args.delay):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    print(f'Images saved in {out_dir}')


if __name__ == '__main__':
    main()
