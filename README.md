# Group-2-Project-2-1
This is the README for our project, by following the instructions below you will be able to display the inital prototype of the eye-tracking parallax effect on a 3D anatomical heart scene. 
As you move your head from left and right in front of the screen a different angle of the heart will be visualized. 

## Requirements
In the `requirements.txt` you can view all the dependencies needed to be downloaded to run the prototype.
Please use a Windows device with a webcam.
Run this in the terminal to download them:
```
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

3. Start the program from the `src` folder :

```
cd src
python main.py
```

With the Panda 3D window at full screen, move your head left and right in front of the screen to view parallax effect. Make sure to press `Esc` to quit.

### Using apply_parallax

Import the function from `parallax.py`:

```python
from parallax import apply_parallax
```

Call this in the Panda3D rendering loop late when `face_found` is True:

```python
apply_parallax(
    self.camera,
    self.camLens,
    position,
    screen_width_cm,
    screen_height_cm,
    camera_offset_y_cm
)
```

Parameters:
- `self.camera`: the Panda3D camera.
- `self.camLens`: the camera lens.
- `position`: the eyetracker's `(x, y, z)` tuple in cm. The function in parallax.py handles the axis conversion.
- `screen_width_cm`: visible display width (excluding borders).
- `screen_height_cm`: visible display height (excluding borders).
- `camera_offset_y_cm`: webcam lens height above the display's centre.

We use 1 scene unit as 1 cm. The screen is at `Y = 0`, so anything with a positive Y is behind the screen. Make sure the rendered view fills the display area you measured.

The function updates both the camera position and projection.

It returns `True` if the view was updated and `False` if there is no position or the distance is 0 or less. Only call it when a face is found, so the view stays in its last position when tracking is lost.