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

keyboard = pyglet.window.key.KeyStateHandler()

# A dictionary containing the images and animations provided by the
# server
# filename -> pyglet object
resources = {}
resources_folder = "/tmp/a_certain_temporary_folder"

# Stores all the game objects
nodes = {}

# A node that represents us specifically
player_node = None

# Connection to the server goes here
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
outbound_packet_buffer = [] # List of shit to remove and send

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
        self.texture_name = texture_name

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
            self.setup_script = base64.b64encode(b"pass").decode()

        # On tick script is called multiply times a second by the server
        if not tick_script_path is None:
            self.tick_script = load_script(self.tick_script_path)
        else:
            self.tick_script = base64.b64encode(b"pass").decode()

    # Turn this node into a packet that the server can view
    def serialize(self):
        return "<NODE>{} {} {} {} {} {} {}".format(
            self.node_id,
            self.x, self.y, self.z,
            self.texture_name,
            self.setup_script, self.tick_script
        )

    def draw(self):
        global resources
        try:
            resources[self.texture_name].blit(self.x, self.y)
        except KeyError as k:
            pass

## LOCAL 
def handle_player_input(dt):
    global player_node
    
    if keyboard[pyglet.window.key.SPACE]:
        print(nodes)

    # Make sure the player exists
    if player_node is None:
        return

    speed = dt*15

    # If he does then you can move him around
    if keyboard[pyglet.window.key.W]:
        player_node.y += speed
        update_player_position()
    if keyboard[pyglet.window.key.A]:
        player_node.x -= speed
        update_player_position()
    if keyboard[pyglet.window.key.S]:
        player_node.y -= speed
        update_player_position()
    if keyboard[pyglet.window.key.D]:
        player_node.x += speed
        update_player_position()

@window.event
def on_draw():
    window.clear()

    for node in nodes.values():
        node.draw()

    if not player_node is None:
        player_node.draw()

def on_tick(dt, t):
    handle_player_input(dt)

## Packet types
def update_player_position():
    packet = "<TRAN>{} {} {} {}\\".format(
        player_node.node_id,
        player_node.x,
        player_node.y,
        player_node.z
    )
    outbound_packet_buffer.append(packet.encode())
    player_node.has_moved = False

def request_node_update():
    outbound_packet_buffer.append("<SEND_NODES>\\".encode())

def spawn_player():
    global player_node
    print("Spawning player...")
    # Spawn our player in
    player_node = Node(
        400.0, 300.0, 0.0,
        '7c03a048d258d84524cdbd49f3f56606e8974f6d53078313eb5f2df390e50427',
        nid=-2
    )
    player_node.has_moved = True

    outbound_packet_buffer.append((player_node.serialize() + "\\").encode())
    print("Done")

def request_resources():
    clientsocket.send("<SEND_RESOURCES>\\".encode())

## Handle communication with server
def on_network_tick(_, __):
    request_node_update()
    update_player_position()

def handle_server_response(packet):
    if packet.startswith("<NODE>"):
        ns = packet.split("<NODE>")
        for node_data_str in ns:
            if node_data_str == '': continue
            nid, x, y, z, texture = node_data_str.split(" ")
            nid = int(nid)
            x, y, z = float(x), float(y), float(z)
            nodes[nid] = Node(x, y, z, texture, nid=nid)
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
        return

    elif packet.startswith("<NODE>"):
        for c in packet.split("<NODE>"):
            if c == "":
                continue
            nid, x, y, z, texture = c.split(" ")
            nid = int(nid)
            x, y, z = float(x), float(y), float(z)
            nodes[nid] = Node(x, y, z, texture, nid=nid)
        return

def recieve_server_response():
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

        # Then actually handle it I guess
        handle_server_response(packet)

def send_client_response():
    while 1:
        if len(outbound_packet_buffer) > 0:
            packet = outbound_packet_buffer.pop(0)
            clientsocket.send(packet)


if __name__ == "__main__":
    # Make sure the resources folder exists
    if not os.path.isdir(resources_folder):
        os.mkdir(resources_folder)

    # Connect to the server
    clientsocket.connect( (sys.argv[1], int(sys.argv[2])) )

    # Start the network handling threads
    recv_thread = threading.Thread(target=recieve_server_response, args=())
    recv_thread.start()

    send_thread = threading.Thread(target=send_client_response, args=())
    send_thread.start()

    # Say hi <3
    request_resources()

    # Then spawn in our player
    spawn_player()

    window.push_handlers(keyboard)
    pyglet.clock.schedule(on_tick, 1.0/20.0)
    pyglet.clock.schedule(on_network_tick, 1.0/10.0)
    pyglet.app.run()
    




