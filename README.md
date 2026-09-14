# Group-2-Project-2-1

## Panda3D prototype setup

This prototype uses Python 3.12 and Panda3D.

### 1. Create a virtual environment

Run this command once from the project folder in the VS Code terminal:

```powershell
py -3.12 -m venv .venv
```

### 2. Select and activate the virtual environment

1. Press `Ctrl + Shift + P` in VS Code.
2. Search for `Python: Select Interpreter`.
3. Select the Python 3.12 interpreter containing `.venv`.
4. Open a new VS Code terminal if necessary.

When the environment is active, the terminal should begin with:

```text
(.venv)
```

### 3. Install the required packages

```powershell
python -m pip install -r requirements.txt
```

## Running the prototype

Make sure the virtual environment is active and run:

```powershell
python main.py
```

A Panda3D window containing the current 3D prototype should open.


# sources
https://docs.panda3d.org/1.10/python/introduction/tutorial/loading-and-animating-the-panda-model