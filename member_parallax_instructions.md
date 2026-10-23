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

It returns True if the view was updated and False if there is no position or the distance is 0 or less. Only call it when a face is found, so the view stays in its last position when tracking is lost.