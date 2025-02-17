import pyglet
class Button:
    def __init__(self, x, y, image_pressed, image_unpressed, callback):
        self.x, self.y = x, y
        self.image_pressed = image_pressed
        self.image_unpressed = image_unpressed
        self.callback = callback

    def draw(self):
        pass
