import os
import time
import random
import base64
import hashlib
import socket

import threading

ip = "127.0.0.1"
port = 8763 + random.randint(0, 10)
node_clock_speed = 1.0/10.0

# Actual TCP socket that we will communicate with the clients on
socket_server = socket.socket()
client_threads = [] # Threads for the connected clients
clients = []

# This will hold filename -> base64encoded file contents
resources = {}

# This will hold all the game objects, called nodes
nodes = {}
total_nodes = 0 # total amount of nodes ever made

class Node:
    def __init__(self, x, y, z, texture, setup_script, tick_script, metadata, nid=None):
        global total_nodes
        # "Texture" here is used somewhat liberally to mean "sha1sum of data we will send to client"
        self.x, self.y, self.z = x, y, z
        self.texture = texture
        self.metadata = metadata

        # They will however have scripts for when they are created
        # and when they are ticked.
        self.setup_script = setup_script
        self.tick_script = tick_script

        # Assign a unique node ID and then increment
        if nid is None:
            self.node_id = total_nodes
            total_nodes += 1
        else:
            self.node_id = nid

        # We'll actually only run the init script the first time the
        # object is ticked, not when we create the object itself
        self.setup_script_has_run = False

    def on_tick(self, dt):
        if not self.setup_script_has_run:
            if not self.setup_script is None:
                exec(self.setup_script)
            self.setup_script_has_run = True
        else:
            if not self.tick_script is None:
                exec(self.tick_script)

    def serialize(self):
        return "{} {} {} {} {} {}".format(
            self.node_id, self.x, self.y, self.z, self.texture,
            base64.b64encode(' '.join([str(i) for i in self.metadata]).encode("utf8")).decode()
        )

    def __str__(self):
        return "<NODE>\n\t{}\n\t{} {} {}\n\t{}\n\t{}\n</NODE".format(
            self.texture, self.x, self.y, self.z, self.setup_script, self.tick_script
        )

# Just call on_tick on every node every howeveroften
def tick_nodes():
    start_time = time.time()
    while 1:
        # Waste CPU cycles while we wait for the tick speed
        while time.time() - start_time < node_clock_speed:
            time.sleep(node_clock_speed/10.0)

        # Tick all the nodes with dt, we'll just do it in this thread
        # for now
        for nid in nodes:
            nodes[nid].on_tick(time.time() - start_time)

        # Then update the starting time for the next dt
        start_time = time.time()

def interact_node(nid, x, y):
    if hasattr(nodes[nid], "on_interact"):
        nodes[nid].on_interact(nodes[nid], x, y)

# Load the resources into a big dictionary of base64 encoded gunk
def load_resources(path):
    files = os.listdir(path)
    for f in files:
        # Images only
        if not f.split(".")[-1] in ["png", "gif", "jpg"]: continue
        # Read the whole image
        d = open(path+"/"+f, 'rb').read()
        na = hashlib.sha1(d).hexdigest()
        resources[na] = base64.b64encode(d)

def send_to_client(client, packet):
    client.send( (packet+"\\").encode() )

def handle_user_command(client, addr, command):
    command = command.strip()
    # Send assets to the user
    if command.startswith("<SEND_RESOURCES>"):
        send_to_client(client, "<RESOURCES>")
        for i in resources:
            send_to_client(client, "{}".format(resources[i].decode("utf8")))
        send_to_client(client, "</RESOURCES>")
        return

    # Allow the user to interact with a node
    elif command.startswith("<INTERACT>"):
        c = command[len("<INTERACT>"):]
        nid, x, y = c.strip().split(" ")
        nid = int(nid)
        x, y = float(x), float(y)
        try:
            interact_node(nid, x, y)
        except Exception as e:
            print(e)

    # Just update a node's position
    elif command.startswith("<MOVE>"):
        # Parse the node information
        c = command[len("<MOVE>"):]
        i, x, y, z = c.split(" ")
        i, x, y, z = int(i), float(x), float(y), float(z)

        # Update the node
        n = nodes[i]
        n.x, n.y, n.z = x, y, z
        return

    elif command.startswith("<ANIM>"):
        # Parse the node information
        c = command[len("<ANIM>"):]
        i, res = c.split(" ")
        i = int(i)
        try:
            nodes[i].texture = res
        except KeyError as e:
            pass

    # Recieve a specific node from the user
    elif command.startswith("<NODE>"):
        c = command[len("<NODE>"):]
        # Chop up the packet
        nid, x, y, z, text, b64a, b64b, metadata = c.split(" ")
        x, y, z = float(x), float(y), float(z)
        nid = int(nid)
        nid = None if nid == -1 else nid # -1 flag for new node

        scripta = base64.b64decode(b64a).decode("utf8")
        scriptb = base64.b64decode(b64b).decode("utf8")
        metadata = base64.b64decode(metadata).decode("utf8")
        metadata = [float(i) for i in metadata.split(" ")]

        # Make it into a new node
        new_node = Node(x, y, z, text, scripta, scriptb, metadata, nid=nid)

        # Store that node in the nodes dictionary
        nodes[new_node.node_id] = new_node

        return

    # SEND ALL THE NODES FUCK YOU FUCK YOU FUCK YOU
    elif command.startswith("<SEND_NODES>"):
        send_to_client(client, "<NODES>")
        for nid in nodes:
            send_to_client(client, nodes[nid].serialize())
        send_to_client(client, "</NODES>")
        return

def handle_socket_connection(client, addr):
    clients.append(client)
    while 1:
        # String parsing? Slow? Never
        packet = ""
        while 1:
            d = client.recv(1)
            if d == b"\\":
                break
            elif d == b'\xff':
                print(addr, "disconnected.")
                clients.remove(client)
                return
            else:
                packet += d.decode("utf8")

        # Print his crap
        #print(packet)

        # Then actually handle it I guess
        try:
            handle_user_command(client, addr, packet)
        except Exception as e:
            print(packet)
            print(e)

def handle_admin_commands():
    while 1:
        print("")
        a = input("> ")
        if not a.strip() == "":
            try:
                exec(a)
            except Exception as e:
                print(e)
        print("")

if __name__ == "__main__":
    # Load in the resources from the resources folder
    load_resources("./resources")

    # Then start going through the threads and updating them
    tick_thread = threading.Thread(target=tick_nodes, args=())
    tick_thread.start()

    admin_panel_thread = threading.Thread(target=handle_admin_commands, args=())
    admin_panel_thread.start()

    # Bind the server to the port and let the admin know
    socket_server.bind((ip, port))
    socket_server.listen(5)
    print("Server is listening on {}:{}".format(ip, port))
    
    # Then start handling every client that connects
    while 1:
        a, b = socket_server.accept()
        client_threads.append(
            threading.Thread(target=handle_socket_connection, args=(a, b))
        )
        client_threads[-1].start()













