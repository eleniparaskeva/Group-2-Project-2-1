import os
from panda3d.core import SamplerState, LineSegs, TransparencyAttrib, TextNode
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.gui import DirectGuiGlobals as DGG

def hex_to_color(hex_string, alpha=1.0):
    hex_string = hex_string.lstrip("#")
    r = int(hex_string[0:2], 16) / 255
    g = int(hex_string[2:4], 16) / 255
    b = int(hex_string[4:6], 16) / 255
    return (r, g, b, alpha)

WHITE = hex_to_color("#FFFFFF")
BLUE = hex_to_color("#173A73")        # background and panels
NAVY = hex_to_color("#0A1A36")        # shadows, webcam frame
RED = hex_to_color("#D62839")         # title shadow, labels, values, progress
DARK_RED = hex_to_color("#5C0A1A")    # shadow under red things
GRID = hex_to_color("#FFFFFF", 0.07)  # background grid lines
TRANSPARENT = (0, 0, 0, 0)


def to_linear(color):
    # simplepbr gamma corrects the window background, so it comes out lighter than the gui, converting the color from sRGB to linear first cancels that out
    result = []
    for c in color[:3]:
        if c <= 0.04045:
            result.append(c / 12.92)
        else:
            result.append(((c + 0.055) / 1.055) ** 2.4)
    return (result[0], result[1], result[2], color[3])

SHADOW_OFFSET = 0.025
BORDER_WIDTH = 0.012

TITLE_FONT_PATH = "resources/fonts/PressStart2P-Regular.ttf"
TEXT_FONT_PATH = "resources/fonts/VT323-Regular.ttf"

title_font = None
text_font = None


def load_font(base, path):
    if not os.path.exists(path):
        print("Font not found: " + path + " (using the default font)")
        return None

    font = base.loader.loadFont(path)
    font.setPixelsPerUnit(80)
    font.setMinfilter(SamplerState.FT_nearest)
    font.setMagfilter(SamplerState.FT_nearest)
    return font


def load_fonts(base):
    # call this once after the ShowBase is created
    global title_font, text_font
    title_font = load_font(base, TITLE_FONT_PATH)
    text_font = load_font(base, TEXT_FONT_PATH)


def make_title(parent, text, pos, scale=0.1, color=WHITE, shadow=RED):
    return OnscreenText(
        parent=parent, text=text, pos=pos, scale=scale,
        fg=color, shadow=shadow, shadowOffset=(0.12, 0.12),
        font=title_font, align=TextNode.ACenter, mayChange=True
    )


def make_text(parent, text, pos, scale=0.07, color=WHITE, align=TextNode.ALeft):
    return OnscreenText(
        parent=parent, text=text, pos=pos, scale=scale,
        fg=color, font=text_font, align=align, mayChange=True
    )


def make_value(parent, text, pos, scale=0.07, align=TextNode.ALeft):
    value = OnscreenText(
        parent=parent, text=text, pos=pos, scale=scale,
        fg=WHITE, bg=RED, font=text_font, align=align, mayChange=True
    )
    value.textNode.setCardAsMargin(0.2, 0.2, 0.1, 0.1)
    return value


def make_label(parent, text, pos, scale=0.04):
    label = OnscreenText(
        parent=parent, text=text, pos=pos, scale=scale,
        fg=WHITE, bg=RED, font=title_font, align=TextNode.ALeft, mayChange=True
    )
    # the text node draws the background box itself, just add some padding
    label.textNode.setCardAsMargin(0.4, 0.4, 0.4, 0.4)
    return label


def pixel_box(parent, left, right, bottom, top, fill=BLUE, border=WHITE, shadow=NAVY):
    shadow_frame = DirectFrame(
        parent=parent, frameColor=shadow,
        frameSize=(left + SHADOW_OFFSET, right + SHADOW_OFFSET, bottom - SHADOW_OFFSET, top - SHADOW_OFFSET)
    )
    if shadow[3] < 1:
        shadow_frame.setTransparency(TransparencyAttrib.MAlpha)
    border_frame = DirectFrame(
        parent=shadow_frame, frameColor=border,
        frameSize=(left, right, bottom, top)
    )
    fill_frame = DirectFrame(
        parent=border_frame, frameColor=fill,
        frameSize=(left + BORDER_WIDTH, right - BORDER_WIDTH, bottom + BORDER_WIDTH, top - BORDER_WIDTH)
    )
    return fill_frame


def make_grid(base, cell_size=0.1):
    aspect = base.getAspectRatio()
    lines = LineSegs("grid")
    lines.setColor(*GRID)
    lines.setThickness(1)

    x = -aspect
    while x <= aspect:
        lines.moveTo(x, 0, -1)
        lines.drawTo(x, 0, 1)
        x = x + cell_size

    y = -1.0
    while y <= 1:
        lines.moveTo(-aspect, 0, y)
        lines.drawTo(aspect, 0, y)
        y = y + cell_size

    grid = base.aspect2d.attachNewNode(lines.create())
    grid.setTransparency(TransparencyAttrib.MAlpha)
    grid.setBin("background", 0)
    return grid


class PixelButton:
    def __init__(self, parent, text, pos, width, height, on_click, on_hover):
        self.text = text
        self.root = parent.attachNewNode("button_" + text)
        self.root.setPos(pos[0], 0, pos[1])

        self.box = pixel_box(self.root, -width / 2, width / 2, -height / 2, height / 2)

        text_scale = height * 0.4
        self.label = OnscreenText(
            parent=self.box, text=text, scale=text_scale,
            pos=(-width / 2 + 0.05, -text_scale * 0.4),
            fg=WHITE, font=title_font, align=TextNode.ALeft, mayChange=True
        )

        self.box["state"] = DGG.NORMAL
        self.box.bind(DGG.B1PRESS, lambda event: on_click())
        self.box.bind(DGG.ENTER, lambda event: on_hover())

    def set_selected(self, selected):
        if selected:
            self.box["frameColor"] = WHITE
            self.label.setFg(RED)
            self.label.setText("> " + self.text)
        else:
            self.box["frameColor"] = BLUE
            self.label.setFg(WHITE)
            self.label.setText("  " + self.text)



def main():
    # small preview of the style
    from direct.showbase.ShowBase import ShowBase

    base = ShowBase()
    base.setBackgroundColor(BLUE)
    load_fonts(base)
    make_grid(base)

    make_title(base.aspect2d, "HEART//PARALLAX", (0, 0.65))

    box = pixel_box(base.aspect2d, -0.7, 0.7, -0.45, 0.35)
    make_text(box, "Sit at a distance of", (-0.62, 0.2))
    make_value(box, "50 cm", (-0.62, 0.07))
    make_text(box, "and hold still.", (-0.38, 0.07))
    pixel_box(box, -0.62, 0.62, -0.25, -0.15, fill=BLUE, border=WHITE, shadow=TRANSPARENT)
    DirectFrame(parent=box, frameColor=RED, frameSize=(-0.6, 0.15, -0.235, -0.165))

    base.accept("escape", base.userExit)
    base.run()


if __name__ == "__main__":
    main()
