"""Data utilities: 3D windowing, patch tokenization, and a synthetic CT+report set."""

from .windowing import window_volume, extract_windows, WindowedVolume
from .synthetic import SyntheticCTReportDataset, generate_synthetic_shard

__all__ = [
    "window_volume",
    "extract_windows",
    "WindowedVolume",
    "SyntheticCTReportDataset",
    "generate_synthetic_shard",
]
