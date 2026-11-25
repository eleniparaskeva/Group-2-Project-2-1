import simplepbr
from direct.showbase.ShowBase import ShowBase
from model.eyetracker import open_config
from tracking import TrackingService
from view import style
from screens.menu_screen import MenuScreen
from screens.launch_screen import LaunchScreen


class App(ShowBase):

    def __init__(self, config):
        super().__init__()

        self.app_config = config

        self.disableMouse() #makes sure mouse does not override parallax effect
        self.camLens.setNearFar(1, 1000) #how far from the camera does panda start and stop drawing set to cm
        simplepbr.init()

        style.load_fonts(self)
        self.grid = style.make_grid(self)
        self.grid.hide()

        self.tracking = TrackingService(config)

        self.screens = {
            "menu": MenuScreen(self),
            "launch": LaunchScreen(self),
        }
        self.current_screen = None
        self.switch_to("menu")

    def switch_to(self, name):
        if self.current_screen is not None:
            self.current_screen.hide()

        self.current_screen = self.screens[name]
        self.current_screen.show()

    def close_app(self):
        # called once when the window closes (not named shutdown, ShowBase already has a shutdown method)
        if self.current_screen is not None:
            self.current_screen.hide()
            self.current_screen = None

        self.tracking.stop()


def main():
    config = open_config()
    app = App(config)

    try:
        app.run()

    finally:
        app.close_app()
        app.destroy()

if __name__ == '__main__':
    main()
