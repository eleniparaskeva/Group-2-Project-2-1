# Group-2-Project-2-1

This is the README for our project, by following the instructions below you will be able to display the inital prototype of the eye-tracking parallax effect on a 3D anatomical heart scene.
As you move your head from left and right in front of the screen a different angle of the heart will be visualized.

## Requirements

In the `requirements.txt` you can view all the dependencies needed to be downloaded to run the prototype.
Please use a Windows device with a webcam.
Run this in the terminal to download them:

``` bash
python -m pip install -r requirements.txt
```

## Run

To run the prototype you need to do the following things:

1. In `config.json` set `"show_visualization"` to `true` to show a debug window of our eyetracking or `false` to hide it
2. In `src/main.py` set the three screen values at the top of `main()` to the one of your monitor in cm

```python
screen_width_cm = ...       # visible display width of your monitor
screen_height_cm = ...   # visible display height of your montior
camera_offset_y_cm = ...    # webcam lens height above the display's centre
```

1. Start the program from the `src` folder :

``` bash
cd src
python main.py
```

With the Panda 3D window at full screen, move your head left and right in front of the screen to view parallax effect. Make sure to press `Esc` to quit.

## Comparing smoothing

Press **F** while the Panda3D window has focus to cycle through raw output,
exponential, adaptive exponential, moving average, weighted moving average,
Butterworth and causal Savitzky-Golay. A popup shows the selected method for two
seconds. Tracking must be running for a selection to take effect.

Every filter keeps receiving the same raw eye positions, including while another
filter is selected. Switching does not reset them. Outputs can differ, so a jump
when switching is expected. Losing the face clears all filter histories; the first
position after reacquisition is used directly. No filter uses future measurements.

Change these settings in `config.json`, then restart:

| Setting | What it does |
| --- | --- |
| `smoothing.adaptive_exponential.alpha` | Adaptive filter's base alpha, from 0 to 1. Lower values smooth more but add lag. |
| `smoothing.adaptive_exponential.speed_gain` | Extra alpha per cm/s of speed. Set to 0 for fixed exponential smoothing. |
| `smoothing.initial_method` | Method selected at startup. |
| `smoothing.cycle_order` | Order of the seven method IDs when pressing the key. Include each once. |
| `smoothing.cycle_key` | Panda3D key name used to cycle methods; defaults to `f`. |
| `smoothing.popup_seconds` | How long the selection popup stays visible. |
| `smoothing.exponential.alpha` | Fixed weight of the new measurement, from 0 to 1. |
| `smoothing.moving_average.window_size` | Number of recent measurements to average. |
| `smoothing.weighted_average.weights` | Non-negative weights, oldest to newest; normalized automatically. |
| `smoothing.butterworth.cutoff_hz` | Cutoff frequency. Lower values smooth more but add lag. |
| `smoothing.butterworth.order` | Positive integer controlling how sharply higher frequencies are rejected. |
| `smoothing.butterworth.sample_rate_hz` | Assumed tracking rate, initially 30 Hz; must exceed twice the cutoff. |
| `smoothing.savitzky_golay.window_size` | Number of recent measurements used for the polynomial fit. |
| `smoothing.savitzky_golay.polynomial_order` | Polynomial degree, from 0 to window size minus 1. |

Alpha 1 means no exponential smoothing. Alpha 0 with speed gain 0 holds the first
position. Window filters repeat the first measurement during startup. Savitzky-Golay
evaluates its fit at the newest sample, which makes it causal, but it can overshoot.
Butterworth can also overshoot. The window filters count tracking samples, and
Butterworth assumes equally spaced samples at the configured rate. If tracking
slows down, their smoothing lasts longer in seconds. Adaptive smoothing measures
speed using actual timestamps, but its base alpha is still per measurement.

The filter implementations and parameter explanations are in `src/smoothing.py`.
To run the filter checks without a camera or Panda3D window:
