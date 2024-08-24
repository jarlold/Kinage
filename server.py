import os
import time
import random
import base64
import hashlib
import socket

import threading

## CONFIG:
ip = "127.0.0.1"
port = 8763 + random.randint(0, 10)
node_clock_speed = 1.0/10.0

## RUNTIME:

# Actual TCP socket that we will communicate with the clients on
socket_server = socket.socket()
client_threads = [] # Threads for the connected clients

# This will hold filename -> base64encoded file contents
resources = {}

# This will hold all the game objects, called nodes
nodes = {}
total_nodes = 0 # total amount of nodes ever made


class Node:
    def __init__(self, x, y, z, texture, setup_script, tick_script, nid=None):
        global total_nodes
        # In our simplified system there will only be image nodes
        # at least for now
        self.x, self.y, self.z = x, y, z
        self.texture = texture

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
        return "<NODE>{} {} {} {} {}".format(
            self.node_id, self.x, self.y, self.z, self.texture
        )

    def __str__(self):
        return "<NODE>\n\t{}\n\t{} {} {}\n\t{}\n\t{}\n</NODE".format(
            self.texture, self.x, self.y, self.z, self.setup_script, self.tick_script
        )


# Load the resources into a big dictionary of base64 encoded gunk
def load_resources(path):
    files = os.listdir(path)
    for f in files:
        # Images only
        if not f.split(".")[-1] in ["png", "gif", "jpg"]: continue
        # Read the whole image
        d = open(path+"/"+f, 'rb').read()
        na = hashlib.sha256(d).hexdigest()
        resources[na] = base64.b64encode(d)


# See if resource is registered in the resources dictionary, if it
# is, send the resource as Bas64 because fuck you
# also try catch is faster here because python is fucked up and fuck
# you fuck you fuck you
def check_resource_exists(resource_name):
    try:
        a = resources[resource_name]
        return True
    except KeyError as e:
        return False


def handle_user_command(client, addr, command):
    command = command.strip()
    if command.startswith("<SEND_RESOURCES>"):
        p = ""
        for i in resources:
            p += "<RESOURCE>" + resources[i].decode("utf8")
            p += ' '
        p += "\\"
        client.send(p.encode())
        return

    elif command.startswith("<SEND_RESOURCE>"):
        c = command[len("<SEND_RESOURCE>"):]
        if check_resource_exists(c):
            p = "<RESOURCE>"+resources[c].decode("utf8")+"\\"
            client.send(p.encode())
        else:
            client.send("<ERROR>404\\".encode())
        return
            

    elif command.startswith("<HEARTBEAT>"):
        client.send("<HEARTBEAT>\\".encode())
        return

    # Just update a node's position
    elif command.startswith("<TRAN>"):
        c = command[len("<TRAN>"):]
        i, x, y, z = c.split(" ")
        i, x, y, z = int(i), float(x), float(y), float(z)
        nodes[i].x = x
        nodes[i].y = y
        nodes[i].z = z

    elif command.startswith("<NODE>"):
        c = command[len("<NODE>"):]
        # Chop up the packet
        nid, x, y, z, text, b64a, b64b = c.split(" ")
        x, y, z = float(x), float(y), float(z)
        nid = int(nid)
        nid = None if nid == -1 else nid # -1 flag for new node

        if b64a == b"None":
            scripta = None
        else:
            scripta = base64.b64decode(b64a).decode("utf8")

        if b64b == b"None":
            scriptb = None
        else:
            scriptb = base64.b64decode(b64b).decode("utf8")

        # Make it into a new node
        new_node = Node(x, y, z, text, scripta, scriptb, nid=nid)

        # Store that node in the nodes dictionary
        nodes[new_node.node_id] = new_node

        # Send it back to the creator so he can update his own list
        #client.send(("<NEW_NODE>{}\\".format(new_node.node_id)+"\\").encode())
        client.send((new_node.serialize()+"\\").encode())
        return

    # SEND ALL THE NODES FUCK YOU FUCK YOU FUCK YOU
    elif command.startswith("<SEND_NODES>"):
        for nid in nodes:
            client.send(nodes[nid].serialize().encode())
        client.send("\\".encode())
        return
        

# Mostly just say hi!
def handle_socket_connection(client, addr):
    # Let the client know what's up
    #client.send("<HEARTBEAT>\\".encode())
    while 1:
        # String parsing? Slow? Never
        packet = ""
        while 1:
            d = client.recv(1)
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
        try:
            handle_user_command(client, addr, packet)
        except Exception as e:
            print(e)


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


if __name__ == "__main__":
    # Load in the resources from the resources folder
    load_resources("./resources")

    # Then start going through the threads and updating them
    tick_thread = threading.Thread(target=tick_nodes, args=())
    tick_thread.start()

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













