# Kinage
*Kinage* stands for *Kinage Is Not A Game Engine*. This is an unfortunate name because Kinage is actually
a really fucked up game engine. Please don't tell anybody.<br>
<p align="center">
   <img src=readme_imgs/strawberry.gif><br>
   I'll give you this strawberry if you keep it a secret okay? ;)
</p>


## History
This is actually the third iteration of an idea I had in highschool while very sick and drinking
Robotussin like it was water. The previous iteration (which was never completed) can be found 
![here](https://github.com/jarlold/GraphicalMultiplayerREPL). Finding the first iteration is left
as an exercise for the reader.<br><br>

The first time I attempted to create this game I had consumed vast quantities of DXM,
and after a brief discussion with the angel Apsinthos, a short time-travel adventure to
shine a blacklight on some ammonia water, and the realization that I can't be real because I'm
not part of the same hologram as the universe, I passed out- and never completed the game.
<br><br>
Ever since it has become my tradition when I am very sick, to attempt to finish this entire thing start to finish.
I always start from scratch, never from the previous version. 
Despite the many previous attempts, this is the first time the end result made it to a playable state. 

## What's it do
Kinage syncs arbitrary "object" definitions across multiple clients and a centralized server.
These objects are sprites with attached Python scripts that run on events (such as a server tick,
interaction, or the node itself being spawned in). Each Python script runs at the same permission
level as the server itself, in the same environment as the server itself, with access to all of
the server's context.

## More Technical Information
Objects are described as `.mas` files. A `.mas` file has three segments (deliniated by `---`):
1. The SHA1 sum of the texture the object should be created with.
2. The setup script, which will be run once the object is created. This section will be
   executed on the server, but never sent to the other clients. More on this later.
4. A metadata section. This is a list of floats that will be sent to clients when the node is serialized.
   The first float in this list is reserved for "node type".

In addition to the "setup script" section, these objects have two other event triggers:
- `on_tick(self, dt)`, called once per server tick
- `on_interact(self, mx, my)` called when the object is interacted (clicked on)
To register these callbacks, simply define them in the setup script.

Here is an example `.mas` file:
```
115561b0e1f6578d0359dc2266e15ee0ef8d8b8f
----
print("fugg")
def on_interact(self, x, y):
    print("thing!")
    self.x += 10

def on_tick(self, dt):
    print("Ticky tock!")

self.on_tick = on_tick
self.on_interact = do_thing
----
0
```

To spawn in the object described by this file, simply drag the file from your file manager and onto the game window.
The `on_tick` function is called by one thread, and it is entirely possible to hog that thread. It is also possible to make
an object that simply deletes the whole server from disk, so fuck it. Eventually, I will add a watchdog thread to stop this
thread from hanging or crashing.

## Theoretical Client Security
The idea is that while *the server* is completely compromised, running a client should
be relatively safe. Relatively. Theoretically. I mean the server could still try directory traversal or something. 
But because the server only serves pre-configured assets (the ones in the `/resources/` folder), and because the clients never execute
arbitrary code (such as scripts) from the server, the client shouldn't be "insecure by design" like the server is.
<br><br>
Also there's no encryption it's just raw TCP lol.

