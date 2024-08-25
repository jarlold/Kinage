import sys
import os
import pyglet
import simplified_client

import pyglet
from pyglet.gl import *

# Pylget state variables
window = pyglet.window.Window(width=800, height=600, fullscreen=False)
keyboard = pyglet.window.key.KeyStateHandler()
pyglet_resources = {}

def load_all_resources():
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    for i in os.listdir(simplified_client.resource_folder):
        img = pyglet.image.load(simplified_client.resource_folder+i)
        pyglet_resources[i] = img

@window.event
def on_draw():
    window.clear()
#   glPushMatrix()
#   glTranslatef(window.width/2.0, window.height/2.0, 0)
#   glTranslatef(-3*simplified_client.player_node.x, -3*simplified_client.player_node.y, 0)
#   glScalef(3.0, 3.0, 1)
    for nid in simplified_client.nodes:
        node = simplified_client.nodes[nid]
        pyglet_resources[node.texture_name].blit(node.x, node.y)
#   glPopMatrix()

def on_tick(dt):
    speed = dt * 40
    if keyboard[pyglet.window.key.W]:
        simplified_client.player_node.y += speed
        simplified_client.player_node.needs_upload = True
    if keyboard[pyglet.window.key.A]:
        simplified_client.player_node.x -= speed
        simplified_client.player_node.needs_upload = True
    if keyboard[pyglet.window.key.S]:
        simplified_client.player_node.y -= speed
        simplified_client.player_node.needs_upload = True
    if keyboard[pyglet.window.key.D]:
        simplified_client.player_node.x += speed
        simplified_client.player_node.needs_upload = True
    if keyboard[pyglet.window.key.SPACE]:
        print(simplified_client.nodes)
        print(simplified_client.player_node.x)

def sync_nodes(_):
    simplified_client.send_nodes()
    simplified_client.download_nodes()

if __name__ == "__main__":
    # Connect to the server
    simplified_client.clientsocket.connect((sys.argv[1], int(sys.argv[2])))

    # Download the resources, then load them into pyglet
    simplified_client.download_resources()
    load_all_resources()

    # Spawn into the world
    simplified_client.spawn_player()

    # Then download the world
    simplified_client.download_nodes()

    # Now lets start setting up pyglet
    window.push_handlers(keyboard)
    pyglet.clock.schedule_interval(on_tick, 1.0/60.0)
    pyglet.clock.schedule_interval(sync_nodes, 1.0/10.0)
    pyglet.app.run()

