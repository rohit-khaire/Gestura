"""Live webcam demo. Press ``q`` in the window to quit.

    python src/realtime.py --camera 0 --threshold 0.8

Needs a GUI build of OpenCV (``pip install opencv-python``), not ``opencv-python-headless``.
"""

import argparse
import logging
import time

import cv2

from inference import Detector, draw_detections

logger = logging.getLogger("realtime")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--checkpoint', default='pretrained/4426_model.pt')
    p.add_argument('--camera', type=int, default=0)
    p.add_argument('--threshold', type=float, default=0.8)
    p.add_argument('--device', default=None, help='cuda / cpu (default: cpu)')
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    detector = Detector(args.checkpoint, threshold=args.threshold, device=args.device)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f'Could not open camera {args.camera}')

    fps = 0.0
    last = time.perf_counter()
    last_logged = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                logger.error('Failed to read a frame from the camera')
                break

            detections = detector(frame)

            # Log when what we see changes, not on every frame.
            seen = tuple(d['label'] for d in detections)
            if seen != last_logged and seen:
                logger.info('detected: %s', ', '.join(f"{d['label']} ({d['score']:.2f})" for d in detections))
            last_logged = seen

            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6) if fps else 1 / max(now - last, 1e-6)
            last = now

            draw_detections(frame, detections)
            cv2.putText(frame, f'{fps:.1f} FPS', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow('Sign detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
