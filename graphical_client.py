import sys
import os
import pyglet
import simplified_client

import magic

import pyglet
from pyglet.gl import *

# Pylget state variables
window = pyglet.window.Window(width=800, height=600, fullscreen=False)
keyboard = pyglet.window.key.KeyStateHandler()
pyglet_resources = {}

player_animation_names = {
    "LEFT":  '299fe3c4ef69bfb82122798bb9e0ad2ebd49222f',
    "RIGHT": '8e5a9c09b0ebd49ed80c27a8809db0816c7530c0',
    "UP":    'c23a9c319fb4c54506e2a1cac1186a62090b4ec6',
    "DOWN":  '10dd15ad708dd7306c01567897b8a16450c38038',
    "IDLE":  '871f349beeddf4f391b51bf03c4e139b4af442fb'
}

def load_all_resources():
    for i in os.listdir(simplified_client.resource_folder):
        # Build the path
        pp = simplified_client.resource_folder+i

        # If the file says its a gif, load it as an animation
        if magic.from_file(pp)[:3] == 'GIF':
            img = pyglet.image.load_animation(
                pp,
                decoder=pyglet.image.codecs.get_animation_decoders()[1]
            )
        # If he says he's a PNG load him as an image
        elif magic.from_file(pp)[:3] == 'PNG': 
            img = pyglet.image.load(simplified_client.resource_folder+i)
        pyglet_resources[i] = pyglet.sprite.Sprite(x=0, y=0, img=img)

@window.event
def on_draw():
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    window.clear()
    glPushMatrix()
    glTranslatef(window.width/2.0, window.height/2.0, 0)
    glTranslatef(-3*simplified_client.player_node.x, -3*simplified_client.player_node.y, 0)
    glScalef(3.0, 3.0, 1)
    nodes_to_draw = list(simplified_client.nodes.values())
    nodes_to_draw.sort(key=lambda x: x.z)
    for node in nodes_to_draw:
        pyglet_resources[node.texture_name].x = node.x
        pyglet_resources[node.texture_name].y = node.y
        pyglet_resources[node.texture_name].draw()
    glPopMatrix()

def on_tick(dt):
    speed = dt * 40
    if keyboard[pyglet.window.key.W]:
        simplified_client.player_node.y += speed
        simplified_client.player_node.needs_upload = True
        simplified_client.set_texture(simplified_client.player_node.node_id, player_animation_names["UP"])

    elif keyboard[pyglet.window.key.S]:
        simplified_client.player_node.y -= speed
        simplified_client.player_node.needs_upload = True
        simplified_client.set_texture(simplified_client.player_node.node_id, player_animation_names["DOWN"])

    elif keyboard[pyglet.window.key.A]:
        simplified_client.player_node.x -= speed
        simplified_client.player_node.needs_upload = True
        simplified_client.set_texture(simplified_client.player_node.node_id, player_animation_names["LEFT"])

    elif keyboard[pyglet.window.key.D]:
        simplified_client.player_node.x += speed
        simplified_client.player_node.needs_upload = True
        simplified_client.set_texture(simplified_client.player_node.node_id, player_animation_names["RIGHT"])
    else:
        simplified_client.set_texture(simplified_client.player_node.node_id, player_animation_names["IDLE"])


    if keyboard[pyglet.window.key.SPACE]:
        print(simplified_client.nodes)

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

