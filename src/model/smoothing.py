"""Causal position filters. Every update uses only measurements seen so far."""

from collections import deque
import math

import numpy as np
from scipy.signal import butter, savgol_coeffs, sosfilt, sosfilt_zi


class ExponentialSmoother:
    """Blend the new position with the previous output on each update.

    alpha is between 0 and 1. Lower values smooth more but add lag; 1 passes
    measurements through. speed_gain is non-negative, in seconds/cm. We use
    alpha = min(1, alpha + speed_gain * speed), with speed measured in cm/s
    between raw positions. A gain of 0.01 adds 0.1 at 10 cm/s. Set it to 0
    for fixed exponential smoothing. All axes use the same weight.
    The first sample is used directly. Repeated or backwards timestamps use
    speed 0. The base smoothing is per measurement, not per second.
    """

    def __init__(self, alpha, speed_gain=0):
        if not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError('alpha must be between 0 and 1')
        if not math.isfinite(speed_gain) or speed_gain < 0:
            raise ValueError('speed_gain must be non-negative')
        self.alpha = alpha
        self.speed_gain = speed_gain
        self.reset()

    def reset(self):
        self.position = self.raw = self.timestamp = None

    def update(self, position, timestamp):
        speed = 0
        if self.timestamp is not None and timestamp > self.timestamp:
            speed = math.dist(position, self.raw) / ((timestamp - self.timestamp) / 1000)
        alpha = min(1, self.alpha + self.speed_gain * speed)
        if self.position is None:
            self.position = tuple(position)
        else:
            self.position = tuple(alpha * x + (1 - alpha) * old
                                  for x, old in zip(position, self.position))
        self.raw, self.timestamp = tuple(position), timestamp
        return self.position


class WindowSmoother:
    """Combine a trailing window with fixed weights, oldest to newest.

    Equal weights give a moving average. Increasing weights give recent
    measurements more influence. The weights are normalized to sum to 1.
    Longer windows usually smooth more and add lag. At startup we repeat the
    first sample to fill the window, so the initial output is that sample.
    Window length is in tracking measurements, not rendering frames or seconds.
    """

    def __init__(self, weights):
        weights = np.asarray(weights, dtype=float)
        if weights.ndim != 1 or not len(weights) or not np.all(np.isfinite(weights)):
            raise ValueError('weights must be a non-empty list of finite numbers')
        if np.any(weights < 0) or weights.sum() <= 0:
            raise ValueError('weights must be non-negative with a positive sum')
        self.weights = weights / weights.sum()
        self.history = deque(maxlen=len(weights))

    def reset(self):
        self.history.clear()

    def update(self, position, timestamp):
        if not self.history:
            self.history.extend([tuple(position)] * self.history.maxlen)
        else:
            self.history.append(tuple(position))
        return tuple(self.weights @ np.asarray(self.history))


class SavitzkyGolaySmoother(WindowSmoother):
    """Fit a polynomial to recent samples and evaluate it at the newest sample.

    window_size is the number of measurements; polynomial_order is the degree
    of the fitted curve and must be smaller than window_size. We evaluate at
    the end, so no future measurements are needed. This follows smooth trends
    but can overshoot and may keep more noise than an average. Samples are
    treated as equally spaced. Startup repeats the first sample.
    """

    def __init__(self, window_size, polynomial_order):
        if type(window_size) is not int or window_size < 1:
            raise ValueError('window_size must be a positive integer')
        if type(polynomial_order) is not int or not 0 <= polynomial_order < window_size:
            raise ValueError('polynomial_order must be between 0 and window_size - 1')
        self.weights = savgol_coeffs(window_size, polynomial_order,
                                    pos=window_size - 1, use='dot')
        self.history = deque(maxlen=window_size)


class ButterworthSmoother:
    """Apply a causal Butterworth low-pass filter independently to each axis.

    cutoff_hz controls how quickly motion can change before it is attenuated.
    Lower cutoffs smooth more and add lag. order controls how sharply higher
    frequencies are rejected; higher orders can add lag and overshoot.
    sample_rate_hz is the assumed tracking rate, not the rendering rate.
    It must exceed twice cutoff_hz. One filter step runs per measurement, so
    if actual tracking rate varies, the effective cutoff varies with it.
    Initial state assumes the first position was held still before tracking.
    """

    def __init__(self, cutoff_hz, order, sample_rate_hz):
        if type(order) is not int or order < 1:
            raise ValueError('Butterworth order must be a positive integer')
        if not all(math.isfinite(x) for x in (cutoff_hz, sample_rate_hz)) or not 0 < cutoff_hz < sample_rate_hz / 2:
            raise ValueError('cutoff_hz must be positive and below half sample_rate_hz')
        self.sos = butter(order, cutoff_hz, fs=sample_rate_hz, output='sos')
        self.reset()

    def reset(self):
        self.state = None

    def update(self, position, timestamp):
        if self.state is None:
            self.state = sosfilt_zi(self.sos)[:, :, None] * np.asarray(position)
        output, self.state = sosfilt(self.sos, [position], axis=0, zi=self.state)
        return tuple(output[0])


class SmoothingComparison:
    """Run every filter on the same raw positions, then select one output.

    cycle_order controls the keybind order; initial_method chooses the startup
    output. Cycling never resets filters. A lost face resets all histories so
    reacquisition starts directly at the new position for every method.
    All timestamps are in milliseconds and positions are in centimeters.
    """

    labels = {
        'raw': 'Raw (no smoothing)',
        'exponential': 'Exponential',
        'adaptive_exponential': 'Adaptive exponential',
        'moving_average': 'Moving average',
        'weighted_average': 'Weighted moving average',
        'butterworth': 'Butterworth',
        'savitzky_golay': 'Causal Savitzky-Golay',
    }

    def __init__(self, config):
        settings = config['smoothing']
        self.order = settings['cycle_order']
        if not self.order or len(set(self.order)) != len(self.order) or set(self.order) != set(self.labels):
            raise ValueError('cycle_order must contain every smoothing method exactly once')
        if settings['initial_method'] not in self.order:
            raise ValueError('initial_method must be in cycle_order')
        self.index = self.order.index(settings['initial_method'])
        size = settings['moving_average']['window_size']
        if type(size) is not int or size < 1:
            raise ValueError('moving average window_size must be a positive integer')
        self.filters = {
            'exponential': ExponentialSmoother(settings['exponential']['alpha']),
            'adaptive_exponential': ExponentialSmoother(**settings['adaptive_exponential']),
            'moving_average': WindowSmoother([1] * size),
            'weighted_average': WindowSmoother(settings['weighted_average']['weights']),
            'butterworth': ButterworthSmoother(**settings['butterworth']),
            'savitzky_golay': SavitzkyGolaySmoother(**settings['savitzky_golay']),
        }
        self.outputs = {}

    @property
    def name(self):
        return self.labels[self.order[self.index]]

    def cycle(self):
        self.index = (self.index + 1) % len(self.order)

    def reset(self):
        for smoother in self.filters.values():
            smoother.reset()
        self.outputs.clear()

    def update(self, position, timestamp):
        self.outputs = {'raw': tuple(position)}
        for name, smoother in self.filters.items():
            self.outputs[name] = smoother.update(position, timestamp)
        return self.outputs[self.order[self.index]]
