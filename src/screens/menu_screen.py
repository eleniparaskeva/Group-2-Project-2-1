from panda3d.core import TextNode
from screens.screen import Screen
from view import style
from view.style import PixelButton

# (button text, screen to switch to), None means not implemented yet
MENU_ITEMS = [
    ("LAUNCH", "launch"),
    ("CALIBRATE", "calibrate"),
    ("EXPERIMENT", None),
    ("QUIT", "quit"),
]


class MenuScreen(Screen):

    def __init__(self, app):
        super().__init__(app)

        left = -app.getAspectRatio()
        style.make_label(self.root, "GROUP 2 / PROJECT 2-1", (left + 0.08, 0.88))

        style.make_title(self.root, "HEART//PARALLAX", (0, 0.5), scale=0.11)
        style.make_text(self.root, "head-tracked 3D anatomy", (0, 0.36), align=TextNode.ACenter)

        self.buttons = []
        y = 0.15
        for i in range(len(MENU_ITEMS)):
            text = MENU_ITEMS[i][0]
            button = PixelButton(
                self.root, text, (0, y), 0.9, 0.13,
                on_click=lambda index=i: self.choose(index),
                on_hover=lambda index=i: self.select(index)
            )
            self.buttons.append(button)
            y = y - 0.19

        self.message = style.make_text(self.root, "", (0, -0.68), align=TextNode.ACenter)
        style.make_text(self.root, "[UP/DOWN] move    [ENTER] select    [ESC] quit", (0, -0.88), scale=0.06, align=TextNode.ACenter)

        self.selected = 0
        self.update_buttons()

    def show(self):
        super().show()
        self.app.setBackgroundColor(style.to_linear(style.BLUE))
        self.app.grid.show()
        self.message.setText("")

        self.accept("arrow_up", self.move, [-1])
        self.accept("arrow_down", self.move, [1])
        self.accept("enter", self.choose_selected)
        self.accept("escape", self.app.userExit)

    def hide(self):
        super().hide()
        self.app.grid.hide()

    def update_buttons(self):
        for i in range(len(self.buttons)):
            self.buttons[i].set_selected(i == self.selected)

    def select(self, index):
        self.selected = index
        self.update_buttons()

    def move(self, step):
        self.select((self.selected + step) % len(self.buttons))

    def choose_selected(self):
        self.choose(self.selected)

    def choose(self, index):
        self.select(index)
        text, target = MENU_ITEMS[index]

        if target == "quit":
            self.app.userExit()
        elif target is None:
            self.message.setText(text + " is not ready yet")
        else:
            self.app.switch_to(target)
