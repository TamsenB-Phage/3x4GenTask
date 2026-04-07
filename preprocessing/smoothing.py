"""
Smoothing utilities for time-series data.

This module provides safe wrappers around common smoothing methods
to ensure robustness when working with noisy or short datasets.
"""

import numpy as np
from scipy.signal import savgol_filter


def safe_savgol(y, window: int = 101, poly: int = 3):
    """
    Safely apply Savitzky-Golay smoothing.

    This function automatically adjusts the window size and avoids
    failures when the input series is too short.

    Parameters
    ----------
    y : array-like
        Input signal.
    window : int, optional (default=101)
        Desired window length for smoothing.
    poly : int, optional (default=3)
        Polynomial order.

    Returns
    -------
    np.ndarray
        Smoothed signal (or original if smoothing is not possible).

    Notes
    -----
    - Ensures window is odd and <= len(y)
    - Prevents invalid configurations (window < poly + 2)
    - Falls back to raw data if smoothing cannot be applied
    """

    y = np.asarray(y)

    # Too little data → return original
    if len(y) < 5:
        return y

    # Ensure window is not larger than data
    window = min(window, len(y))

    # Window must be odd
    if window % 2 == 0:
        window -= 1

    # Ensure valid polynomial relationship
    if window < poly + 2:
        return y

    try:
        return savgol_filter(y, window_length=window, polyorder=poly)
    except Exception:
        # Fallback safety (rare edge cases)
        return y