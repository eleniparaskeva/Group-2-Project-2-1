from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import AmbientLight, DirectionalLight, TransparencyAttrib, PointLight
import simplepbr
from parallax import apply_parallax

class HeartApp(ShowBase): #modified to fit screen values needed in apply_parallax
    def __init__(self, screen_width_cm, screen_height_cm, camera_offset_y_cm):
        super().__init__()

        self.screen_width_cm = screen_width_cm
        self.screen_height_cm = screen_height_cm
        self.camera_offset_y_cm = camera_offset_y_cm
        self.head_position = None
        self.smoothing_popup = OnscreenText(
            text='', pos=(0, 0.85), scale=0.055,
            fg=(1, 1, 1, 1), bg=(0, 0, 0, 0.75), mayChange=True
        )
        self.smoothing_popup.hide()
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

        #Create a parent for the anatomical models
        self.anatomy = self.render.attachNewNode("anatomy")
        
        # Load the anatomical heart
        self.heart = self.loader.loadModel(
            "../models/human_heart_internal_structure_3d_model.glb"
        )

        if self.heart.isEmpty():
            print("ERROR: Heart model could not be loaded.")
            return

        self.heart.reparentTo(self.anatomy)

        # Scale the heart
        self.heart.setScale(7)

        # Position the heart
        self.heart.setPos(5, 10, 2)

        # Keep the current orientation
        self.heart.setHpr(-90, 0, 0)

        #Load the ribcage 
        self.ribs = self.loader.loadModel(
            "../models/chest.glb"
        )

        if self.ribs.isEmpty():
            print("ERROR:Ribs model could not be loaded.")
        else: 
            self.ribs.reparentTo(self.anatomy)

        #Initial scale and position (will need adjustment)
        self.ribs.setScale(40)
        self.ribs.setPos(2, 8, 0)
        self.ribs.setHpr(0, 0, 0)

        #make the rib cage semi-transparent 
        self.ribs.setTransparency(TransparencyAttrib.MAlpha)

        #light blue colour with trannsparency
        self.ribs.setColor(0.55, 0.85, 1.0, 1.0)

        #enable transparency 
        self.ribs.setAlphaScale(0.35)

        #left blue side light (we can remove it we don't like it )
        left_light = PointLight("left_blue_light")
        left_light.setColor((0.35, 0.7, 1.0, 1))

        left_light_np = self.anatomy.attachNewNode(left_light)
        left_light_np.setPos(-12, 0, 0)

        self.ribs.setLight(left_light_np)

        #right blue side light 
        right_light = PointLight("right_blue_light")
        right_light.setColor((0.35, 0.7, 1.0, 1))

        right_light_np = self.anatomy.attachNewNode(right_light)
        right_light_np.setPos(12, 0, 0)

        self.ribs.setLight(right_light_np)

        # Temporary color so we can clearly see the geometry
        # self.heart.setColor(0.8, 0.1, 0.1, 1)
        #self.heart.setTwoSided(True)

        # Background
        self.setBackgroundColor(0.003, 0.012, 0.05)

        # Mouse interaction
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)

        self.taskMgr.add(self.rotate_anatomy, "rotate_anatomy")
        self.taskMgr.add(self.update_parallax, "update_parallax")

    def show_smoothing_popup(self, name, duration):
        """Show the selected filter briefly, restarting the timer on each change.

        duration is the popup lifetime in seconds. This runs on the rendering
        thread after the tracker confirms which method supplies its output.
        """
        self.smoothing_popup.setText('Smoothing: ' + name)
        self.smoothing_popup.show()
        self.taskMgr.remove('hide_smoothing_popup')
        self.taskMgr.doMethodLater(duration, self.hide_smoothing_popup, 'hide_smoothing_popup')

    def hide_smoothing_popup(self, task):
        self.smoothing_popup.hide()
        return task.done

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

    def rotate_anatomy(self, task):

        if self.dragging and self.mouseWatcherNode.hasMouse():

            mouse = self.mouseWatcherNode.getMouse()

            current_x = mouse.getX()
            current_y = mouse.getY()

            # Calculate mouse movement
            dx = current_x - self.last_mouse_x
            dy = current_y - self.last_mouse_y

            # Rotate the heart
            #put 40 for now so that is doesn't move to fast
            self.anatomy.setH(
                self.anatomy.getH() - dx * 80
            )

            self.anatomy.setP(
                self.anatomy.getP() + dy * 80
            )

            # Remember current mouse position
            self.last_mouse_x = current_x
            self.last_mouse_y = current_y

        return task.cont
