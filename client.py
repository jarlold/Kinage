import base64

import pyglet
from pyglet.gl import *

## CONFIG:
window_width = 800
window_height = 600

# Pyglet context window
window = pyglet.window.Window(
    width=window_width,
    height=window_height,
    fullscreen=False
)

# Stores all the game objects
nodes = []

# Load a script off of disk, and encode it for the server
def load_script(path):
    opn = open(path, 'rb')
    s = opn.read()
    s = base64.b64encode(s).decode()
    return s


class Node:
    def __init__(self, x, y, z, texture_name, setup_script_path=None, tick_script_path=None, nid=None):
        global total_nodes
        self.x, self.y, self.z = x, y, z
        self.texture_name = texture

        # If there's no node id then it will be -1, a flag to the server
        # meaning "this is a new node"
        if nid is None:
            self.node_id = -1
        else:
            self.node_id = nid

        # If we specify a script path, then we'll load the script from disk
        # into memory, and encode it for the server.
        # On setup script is called by the server for the first tick and only
        # the first script
        if not setup_script_path is None:
            self.setup_script = load_script(self.setup_script_path)
        else:
            self.setup_script = None

        # On tick script is called multiply times a second by the server
        if not self.tick_script_path is None:
            self.tick_script = load_script(self.tick_script_path)
        else:
            self.tick_script = None

    # Turn this node into a packet that the server can view
    def serialize(self):
        return "<NODE>{} {} {} {} {} {} {}".format(
            self.node_id,
            self.x, self.y, self.z,
            self.texture_name,
            self.setup_script, self.tick_script
        )


if __name__ == "__main__":
    print(load_script("./test.txt"))
    pyglet.app.run()
    




