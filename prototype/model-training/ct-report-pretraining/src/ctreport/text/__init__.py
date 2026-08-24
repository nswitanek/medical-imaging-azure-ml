"""Text tokenization for the CT–report text tower.

The tokenizer is *paired* with the text encoder (see ``models/text_encoder.py``):
``"qwen"`` uses the real Qwen3 tokenizer, ``"fallback"`` uses the dependency-free
controlled-vocabulary tokenizer. ``build_tokenizer(cfg, kind)`` returns the matching one.
"""

from .tokenizer import (
    TextTokenizer,
    QwenTokenizer,
    FallbackTokenizer,
    build_tokenizer,
    resolve_text_model_ref,
)

__all__ = [
    "TextTokenizer",
    "QwenTokenizer",
    "FallbackTokenizer",
    "build_tokenizer",
    "resolve_text_model_ref",
]
