import logging
import math

import torch
from torch import nn
from torchvision.models import ResNet50_Weights, resnet50

logger = logging.getLogger(__name__)


def _get_1d_sincos_pos_embed(length: int, dim: int, temperature: float = 10000.0, device=None):
    assert dim % 2 == 0
    position = torch.arange(length, device=device, dtype=torch.float32).unsqueeze(1)  # (L,1)
    div_term = torch.exp(
        torch.arange(0, dim, 2, device=device, dtype=torch.float32) * (-math.log(temperature) / dim)
    )  # (dim/2)
    pe = torch.zeros(length, dim, device=device, dtype=torch.float32)
    pe[:, 0::2] = torch.sin(position * div_term)
    pe[:, 1::2] = torch.cos(position * div_term)
    return pe  # (L, dim)


def build_2d_sincos_position_embedding(height: int, width: int, dim: int, device=None):
    """Create 2D sine-cos positional encoding of shape (1, H*W, dim).
    Half dims for Y, half for X.
    """
    assert dim % 2 == 0, "positional dim must be even"
    dim_half = dim // 2
    pe_y = _get_1d_sincos_pos_embed(height, dim_half, device=device)  # (H, dim/2)
    pe_x = _get_1d_sincos_pos_embed(width, dim_half, device=device)  # (W, dim/2)
    # Combine to (H, W, dim)
    pos = torch.zeros(height, width, dim, device=device, dtype=torch.float32)
    pos[:, :, :dim_half] = pe_y[:, None, :].expand(-1, width, -1)
    pos[:, :, dim_half:] = pe_x[None, :, :].expand(height, -1, -1)
    return pos.view(1, height * width, dim)  # (1, H*W, dim)


class DETR(nn.Module):
    """Small DETR: ResNet-50 backbone + 1 encoder / 1 decoder layer + 25 object queries.

    ``pretrained_backbone=True`` downloads the ImageNet weights, which is what you want when
    training from scratch. For inference (or when resuming from a checkpoint) pass ``False``:
    the checkpoint already contains every weight, so the download would be wasted.
    """

    def __init__(self, num_classes, hidden_dim=256, nheads=8,
                 num_encoder_layers=1, num_decoder_layers=1, num_queries=25,
                 pretrained_backbone=True):
        super().__init__()

        # create ResNet-50 backbone
        weights = ResNet50_Weights.IMAGENET1K_V1 if pretrained_backbone else None
        self.backbone = resnet50(weights=weights)
        self.backbone.fc = nn.Identity()

        # create conversion layer
        self.conv = nn.Conv2d(2048, hidden_dim, 1)

        # create a default PyTorch transformer
        self.transformer = nn.Transformer(
            hidden_dim, nheads, num_encoder_layers, num_decoder_layers, batch_first=True, dropout=0.1)

        # prediction heads, one extra class for predicting non-empty slots
        # note that in baseline DETR linear_bbox layer is 3-layer MLP
        self.linear_class = nn.Linear(hidden_dim, num_classes + 1)
        self.linear_bbox = nn.Linear(hidden_dim, 4)

        # number of object queries
        self.num_queries = num_queries
        # learned query positional encodings
        self.query_pos = nn.Parameter(torch.randn(self.num_queries, hidden_dim))

        # normalizations
        self.norm_src = nn.LayerNorm(hidden_dim)
        self.norm_tgt = nn.LayerNorm(hidden_dim)

    def forward(self, inputs):
        # propagate inputs through ResNet-50 up to the last conv stage
        x = self.backbone.conv1(inputs)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)

        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)

        # convert from 2048 to hidden_dim feature planes for the transformer
        feat = self.conv(x)  # (b, d, Hf, Wf)
        bsz, d_model, Hf, Wf = feat.shape
        src = feat.flatten(2).permute(0, 2, 1)  # (b, Hf*Wf, d)

        # dynamic 2D sine-cos positional encoding
        pos = build_2d_sincos_position_embedding(Hf, Wf, d_model, device=feat.device)  # (1, Hf*Wf, d)
        src = self.norm_src(src + pos)

        # decoder target: zero content + learned query positional encodings
        tgt = torch.zeros(bsz, self.num_queries, d_model, device=feat.device)
        query_pos = self.query_pos.unsqueeze(0).expand(bsz, -1, -1)
        tgt = self.norm_tgt(tgt + query_pos)

        # propagate through the transformer
        hs = self.transformer(src=src, tgt=tgt)  # (b, num_queries, d)

        # finally project transformer outputs to class labels and bounding boxes
        return {
            'pred_logits': self.linear_class(hs),
            'pred_boxes': self.linear_bbox(hs).sigmoid()
        }

    def count_parameters(self):
        """Return (total, trainable) parameter counts."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return total, trainable

    def _expand_class_head(self, state):
        """Grow a checkpoint's classification head to this model's class count.

        ``linear_class`` has ``num_classes + 1`` outputs; the LAST one is "no object". Rows of the
        classes the checkpoint already knows (the first ``old`` classes) and its "no object" row are
        kept, the rows of the new classes keep this model's fresh initialisation. So new signs must
        be APPENDED to ``config.json`` (never reordered) and then trained on.
        """
        weight, bias = state["linear_class.weight"], state["linear_class.bias"]
        old = weight.shape[0] - 1
        new = self.linear_class.out_features - 1
        if old == new:
            return state
        if old > new:
            raise ValueError(f"checkpoint has {old} classes but config.json lists only {new}")

        new_weight = self.linear_class.weight.detach().clone()
        new_bias = self.linear_class.bias.detach().clone()
        new_weight[:old], new_bias[:old] = weight[:old], bias[:old]
        new_weight[-1], new_bias[-1] = weight[-1], bias[-1]  # "no object"
        state = dict(state)
        state["linear_class.weight"], state["linear_class.bias"] = new_weight, new_bias
        return state

    def load_pretrained(self, checkpoint_path, map_location="cpu", expand_head=False):
        """Load a state_dict checkpoint.

        Raises if the file is missing or doesn't match this architecture. (It used to log the
        error and carry on, which silently left the model with random weights.)

        With ``expand_head=True`` a checkpoint trained on FEWER classes is accepted: its weights are
        loaded and the classification head is grown (see ``_expand_class_head``). Use this to add
        signs to an existing model by fine-tuning.
        """
        state = torch.load(checkpoint_path, map_location=map_location, weights_only=True)
        if expand_head:
            state = self._expand_class_head(state)
        self.load_state_dict(state)
        logger.info("Loaded checkpoint %s", checkpoint_path)
        return self

if __name__ == '__main__':
    total, trainable = DETR(num_classes=3, pretrained_backbone=False).count_parameters()
    print(f"parameters: {total:,} total, {trainable:,} trainable")
