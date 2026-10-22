from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight
import simplepbr
from parallax import apply_parallax

class HeartApp(ShowBase): #modified to fit screen values needed in apply_parallax
    def __init__(self, screen_width_cm, screen_height_cm, camera_offset_y_cm):
        super().__init__()

        self.screen_width_cm = screen_width_cm
        self.screen_height_cm = screen_height_cm
        self.camera_offset_y_cm = camera_offset_y_cm
        self.head_position = None
        self.disableMouse() #makes sure mouse does not override parallax effect
        self.camLens.setNearFar(1,1000) #how far from the camera does panda start and stop drawing set to cm

        simplepbr.init()

        # Ambient light
        ambient = AmbientLight("ambient")
        ambient.setColor((0.4, 0.4, 0.4, 1))
        ambient_np = render.attachNewNode(ambient)
        render.setLight(ambient_np)

        # Main directional light
        directional = DirectionalLight("directional")
        directional.setColor((1, 1, 1, 1))
        directional_np = render.attachNewNode(directional)
        directional_np.setHpr(-45, -30, 0)
        render.setLight(directional_np)

        # Load the anatomical heart
        self.heart = self.loader.loadModel(
            "../models/realistic_human_heart.glb"
        )

        if self.heart.isEmpty():
            print("ERROR: Heart model could not be loaded.")
            return

        self.heart.reparentTo(self.render)

        # Scale the heart
        self.heart.setScale(11)

        # Position the heart
        self.heart.setPos(0, 8, 0)

        # Keep the current orientation
        self.heart.setHpr(0, 0, 0)

        # Temporary color so we can clearly see the geometry
        # self.heart.setColor(0.8, 0.1, 0.1, 1)
        #self.heart.setTwoSided(True)

        # Background
        self.setBackgroundColor(0.08, 0.08, 0.08)

        # Mouse interaction
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)

        self.taskMgr.add(self.rotate_heart, "rotate_heart")
        self.taskMgr.add(self.update_parallax, "update_parallax")

    def set_head_position(self, position):
        self.head_position = position

    def update_parallax(self, task): #added apply_parallax method
        if self.head_position is not None:
            apply_parallax(self.camera, self.camLens, self.head_position, self.screen_width_cm, self.screen_height_cm, self.camera_offset_y_cm)
        return task.cont

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            mouse = self.mouseWatcherNode.getMouse()

            self.dragging = True
            self.last_mouse_x = mouse.getX()
            self.last_mouse_y = mouse.getY()

    def stop_drag(self):
        self.dragging = False

    def rotate_heart(self, task):

        if self.dragging and self.mouseWatcherNode.hasMouse():

            mouse = self.mouseWatcherNode.getMouse()

            current_x = mouse.getX()
            current_y = mouse.getY()

            # Calculate mouse movement
            dx = current_x - self.last_mouse_x
            dy = current_y - self.last_mouse_y

            # Rotate the heart
            #put 40 for now so that is doesn't move to fast
            self.heart.setH(
                self.heart.getH() - dx * 80
            )

            self.heart.setP(
                self.heart.getP() + dy * 80
            )

            # Remember current mouse position
            self.last_mouse_x = current_x
            self.last_mouse_y = current_y

        return task.cont
