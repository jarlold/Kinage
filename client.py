import os
import base64
import sys
import socket
import hashlib

import threading

import pyglet
from pyglet.gl import *
from pyglet import image

## CONFIG:
window_width = 800
window_height = 600

# Pyglet context window
window = pyglet.window.Window(
    width=window_width,
    height=window_height,
    fullscreen=False
)

# A dictionary containing the images and animations provided by the
# server
# filename -> pyglet object
resources = {}
resources_folder = "/tmp/a_certain_temporary_folder"

# Stores all the game objects
nodes = {}

# Connection to the server goes here
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Load a script off of disk, and encode it for the server
def load_script(path):
    opn = open(path, 'rb')
    s = opn.read()
    s = base64.b64encode(s).decode()
    return s

def load_resource(name, path):
    resources[name] = image.load(path)


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

    def draw(self):
        resources[self.texture_name].blit(self.x, self.y)


@window.event
def on_draw():
    for i in resources:
        resources[i].blit(window_width/2, window_height/2)

    for node in nodes.values():
        node.draw()


def handle_server_response(packet):
    print(packet[:20])
    print("HANDLING")
    if packet.startswith("<NODE>"):
        ns = packet.split("<NODE>")
        for node_data_str in ns:
            nid, x, y, z, texture = node_data_str.split(" ")
            nid = int(nid)
            x, y, z = float(x), float(y), float(z)
            node[i] = Node(x, y, z, texture, nid=nid)
        return

    elif packet.startswith("<RESOURCE>"):
        for c in packet.split("<RESOURCE>"):
            if c == "":
                continue
            resource_bin = base64.b64decode(c)
            pp = resources_folder + "/" + hashlib.sha256(resource_bin).hexdigest()
            with open(pp, 'wb') as opn:
                opn.write(resource_bin)
                opn.close()
            load_resource(hashlib.sha256(resource_bin).hexdigest(), pp)
        print(resources)
        return

    #elif packet.startswith("<HEARTBEAT>"):
        #clientsocket.send("<HEARTBEAT>\\".encode())


def handle_socket_connection():
    # Let the client know what's up
    clientsocket.send("<HEARTBEAT>\\".encode())
    while 1:
        # String parsing? Slow? Never
        packet = ""
        while 1:
            d = clientsocket.recv(1)
            if d == b"\\":
                break
            elif d == b'\xff':
                print(addr, "disconnected.")
                return
            else:
                packet += d.decode("utf8")

        # Print his crap
        #print(packet)

        # Then actually handle it I guess
        handle_server_response(packet)
    

if __name__ == "__main__":
    # Make sure the resources folder exists
    if not os.path.isdir(resources_folder):
        os.mkdir(resources_folder)

    # Connect to the server
    clientsocket.connect( (sys.argv[1], int(sys.argv[2])) )

    # Say hi <3
    #clientsocket.send("<HEARTBEAT>\\".encode()) # thats how we say hi here
    clientsocket.send("<SEND_RESOURCES>\\".encode()) # thats how we say hi here

    socket_thread = threading.Thread(target=handle_socket_connection, args=())
    socket_thread.start()

    # Load in some resources
    #load_resource("a", "./resources/1.png")
    #print(resources)

    pyglet.app.run()
    




