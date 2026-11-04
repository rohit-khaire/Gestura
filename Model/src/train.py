"""Train or fine-tune the DETR sign detector.

Examples (run from the ``Model`` directory):

    python src/train.py                                        # from ImageNet backbone
    python src/train.py --resume pretrained/4426_model.pt      # fine-tune an existing model
    python src/train.py --resume pretrained/4426_model.pt --expand-head   # ...after adding new signs

Data layout: ``data/train/{images,labels}`` and ``data/test/{images,labels}`` (YOLO labels).
"""

import argparse
import logging
import time
from pathlib import Path

import torch
from torch import optim
from torch.utils.data import DataLoader

from data import DETRData
from loss import DETRLoss, HungarianMatcher
from model import DETR
from utils.boxes import stacker
from utils.setup import get_classes

logger = logging.getLogger("train")

LOSS_WEIGHTS = {'class_weighting': 1, 'bbox_weighting': 5, 'giou_weighting': 2}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data', default='data', help='folder containing train/ and test/')
    p.add_argument('--resume', default=None, help='checkpoint to start from (fine-tuning)')
    p.add_argument('--expand-head', action='store_true',
                   help='allow --resume from a checkpoint with fewer classes (adding new signs)')
    p.add_argument('--checkpoints', default='checkpoints', help='where to write checkpoints')
    p.add_argument('--epochs', type=int, default=100)
    p.add_argument('--batch-size', type=int, default=4)
    p.add_argument('--lr', type=float, default=1e-5)
    p.add_argument('--weight-decay', type=float, default=1e-4)
    p.add_argument('--grad-clip', type=float, default=0.1, help='max gradient norm (0 disables)')
    p.add_argument('--restart-epochs', type=int, default=30, help='first cosine-annealing cycle length, in epochs')
    p.add_argument('--save-every', type=int, default=10, help='also keep a checkpoint every N epochs')
    p.add_argument('--workers', type=int, default=0, help='DataLoader worker processes')
    p.add_argument('--device', default=None, help='cuda / cpu (default: cuda if available)')
    p.add_argument('--seed', type=int, default=0)
    return p.parse_args()


def run_epoch(model, loader, criterion, device, optimizer=None, grad_clip=0.0):
    """One pass over ``loader``; trains if an optimizer is given, otherwise just evaluates.
    Returns the mean weighted loss per batch."""
    training = optimizer is not None
    model.train(training)
    total = 0.0
    with torch.set_grad_enabled(training):
        for images, targets in loader:
            images = images.to(device)
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

            loss = criterion.total_loss(criterion(model(images), targets))

            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                optimizer.step()
            total += loss.item()
    return total / max(len(loader), 1)


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    torch.manual_seed(args.seed)

    device = torch.device(args.device or ('cuda' if torch.cuda.is_available() else 'cpu'))
    num_classes = len(get_classes())

    train_loader = DataLoader(DETRData(Path(args.data) / 'train'), batch_size=args.batch_size, shuffle=True,
                              collate_fn=stacker, drop_last=True, num_workers=args.workers)
    test_loader = DataLoader(DETRData(Path(args.data) / 'test', train=False), batch_size=args.batch_size,
                             collate_fn=stacker, num_workers=args.workers)
    if len(train_loader) == 0:
        raise SystemExit(f'Need at least {args.batch_size} training images in {args.data}/train')

    # Only fetch the ImageNet backbone weights when we are not resuming from a checkpoint.
    model = DETR(num_classes=num_classes, pretrained_backbone=args.resume is None)
    if args.resume:
        model.load_pretrained(args.resume, expand_head=args.expand_head)
    model.to(device)

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    # Stepped once per epoch, so T_0 is measured in epochs.
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=args.restart_epochs, T_mult=2)
    criterion = DETRLoss(num_classes=num_classes, matcher=HungarianMatcher(LOSS_WEIGHTS),
                         weight_dict=LOSS_WEIGHTS, eos_coef=0.1).to(device)

    total_params, trainable_params = model.count_parameters()
    logger.info('device=%s  classes=%d  params=%s (%s trainable)  train batches=%d  test batches=%d',
                device, num_classes, f'{total_params:,}', f'{trainable_params:,}',
                len(train_loader), len(test_loader))

    ckpt_dir = Path(args.checkpoints)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_test_loss = float('inf')

    for epoch in range(1, args.epochs + 1):
        started = time.time()
        train_loss = run_epoch(model, train_loader, criterion, device, optimizer, args.grad_clip)
        lr = optimizer.param_groups[0]['lr']
        scheduler.step()
        test_loss = run_epoch(model, test_loader, criterion, device) if len(test_loader) else float('nan')

        logger.info('epoch %d/%d  train %.4f  test %.4f  lr %.2e  %.0fs',
                    epoch, args.epochs, train_loss, test_loss, lr, time.time() - started)

        if test_loss < best_test_loss:
            best_test_loss = test_loss
            torch.save(model.state_dict(), ckpt_dir / 'best_model.pt')
        if args.save_every and epoch % args.save_every == 0:
            torch.save(model.state_dict(), ckpt_dir / f'{epoch}_model.pt')

    torch.save(model.state_dict(), ckpt_dir / 'last_model.pt')
    logger.info('done. best test loss %.4f -> %s', best_test_loss, ckpt_dir / 'best_model.pt')


if __name__ == '__main__':
    main()
