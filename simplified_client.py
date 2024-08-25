import sys
import random
import socket
import base64
import hashlib
from client_node import Node

# Holds all the game objects 
nodes = {}
player_node = None # Overwrite later

# Holds all the game resources
resource_folder = "/tmp/a_certain_temporary_folder/"

# TCP connection to the server
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def recv_packet():
    # String parsing? Slow? Never
    packet = ""
    while 1:
        data = clientsocket.recv(1)
        if data == b"\\":
            break
        if data == b'\xff':
            print("disconnected.")
            return
        packet += data.decode("utf8")
    return packet

def send_packet(packet):
    clientsocket.send((packet+"\\").encode())

def save_resource(contents):
    resource_name = hashlib.sha1(contents).hexdigest()
    opn = open(resource_folder + resource_name, 'wb')
    opn.write(contents)
    opn.close()

def load_template(p):
    opn = open(p, 'r')
    contents = opn.read()
    opn.close()
    texture_name, setup_script, tick_script, metadata = contents.split("----")
    texture_name = texture_name.strip()
    setup_script = setup_script.strip()
    tick_script = tick_script.strip()
    metadata = metadata.strip()
    t = {
        "texture": texture_name,
        "setup_script": setup_script,
        "tick_script": tick_script,
        "metadata": [float(i) for i in metadata.split(" ")]
    }
    return t

def spawn_template_file(p, x, y, z):
    f = load_template(p)
    n = Node(
        x, y, z,
        f["texture"],
        f["metadata"],
        setup_script=f["setup_script"],
        tick_script=f["tick_script"]
    )
    print(n.serialize())
    send_packet(n.serialize())
    download_nodes()

def send_nodes():
    for nid in nodes:
        node = nodes[nid]
        if node.needs_upload:
            send_packet(node.serialize())
            node.needs_upload = False

def download_nodes():
    global player_node
    send_packet("<SEND_NODES>")
    packet = recv_packet()
    while (packet := recv_packet()) != "</NODES>":
        nid, x, y, z, text, metadata = packet.split(" ")
        nid = int(nid)
        # Dont let other people overwrite our player controls!
        if not player_node is None and nid == player_node.node_id:
            continue
        metadata = base64.b64decode(metadata).decode("utf8")
        metadata = [float(i) for i in metadata.split(" ")]
        x, y, z = float(x), float(y), float(z)
        new_node = Node(x, y, z, text, metadata, nid=nid)
        nodes[nid] = new_node

def download_resources():
    send_packet("<SEND_RESOURCES>")
    packet = recv_packet()
    while (packet := recv_packet()) != "</RESOURCES>":
        content = base64.b64decode(packet)
        save_resource(content)

def move_node(nid, x, y, z):
    n = nodes[nid]
    n.x, n.y, n.z = x, y, z
    n.needs_upload = True

def set_texture(nid, texture):
    nodes[nid].texture_name = texture
    send_packet("<ANIM>{} {}".format(nid, texture))

def spawn_player():
    global player_node
    player_node = Node(
        0.0, 0.0, 0.0,
        "47fc0a0b352b61dea11e4137aeb7550160df01a2",
        [0],
        nid=-2 - random.randint(1, 100),
    )
    player_node.needs_upload = True
    nodes[player_node.node_id] = player_node

def print_nodes():
    for i in nodes:
        print(nodes[i])


if __name__ == "__main__":
    # Connect to the server
    clientsocket.connect((sys.argv[1], int(sys.argv[2])))

    # Download the resources
    download_resources()

    # Download the current game world data
    download_nodes()

    # Then drop into a command prompt
    while 1:
        print("")
        a = input("> ")
        try:
            exec(a)
        except Exception as e:
            print(e)








