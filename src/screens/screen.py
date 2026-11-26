from direct.showbase.DirectObject import DirectObject


class Screen(DirectObject):
    # base class for all screens, the App calls show() and hide() when switching

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.root = app.aspect2d.attachNewNode(type(self).__name__)
        self.root.hide()

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()
        self.ignoreAll()
