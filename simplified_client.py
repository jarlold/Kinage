import sys
import random
import socket
import base64
import hashlib
from client_node import Node

# Holds all the game objects 
nodes = {}
player_node = [] # Overwrite later

# Holds all the game resources
resources = {}

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

def send_nodes():
    for nid in nodes:
        node = nodes[nid]
        if node.needs_upload:
            send_packet(node.serialize())
            node.needs_upload = False

def download_nodes():
    send_packet("<SEND_NODES>")
    packet = recv_packet()
    while (packet := recv_packet()) != "</NODES>":
        print(packet)
        nid, x, y, z, text = packet.split(" ")
        nid = int(nid)
        x, y, z = float(x), float(y), float(z)
        new_node = Node(x, y, z, text, nid=nid)
        nodes[nid] = new_node

def download_resources():
    send_packet("<SEND_RESOURCES>")
    packet = recv_packet()
    while (packet := recv_packet()) != "</RESOURCES>":
        content = base64.b64decode(packet)
        s = hashlib.sha1(content).hexdigest()
        resources[s] = content

def move_node(nid, x, y, z):
    n = nodes[nid]
    n.x, n.y, n.z = x, y, z
    n.needs_upload = True

def spawn_player():
    player_node = Node(
        0.0, 0.0, 0.0,
        '7c03a048d258d84524cdbd49f3f56606e8974f6d53078313eb5f2df390e50427',
        nid=-2 - random.randint(1, 100)
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








