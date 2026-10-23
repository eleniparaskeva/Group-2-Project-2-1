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
