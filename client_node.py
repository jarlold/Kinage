import base64
import random

class Node:
    def __init__(self, x, y, z, texture_name, metadata, setup_script=None, tick_script=None, nid=None):
        global total_nodes
        self.x, self.y, self.z = x, y, z
        self.texture_name = texture_name
        self.metadata = metadata

        # If there's no node id then it will be -1, a flag to the server
        # meaning "this is a new node"
        if nid is None:
            self.node_id = -1
        else:
            self.node_id = nid

        # Whether or not the node needs to be re-sent to the server
        self.needs_upload = False

        # Not deleted... yet...
        self.deleted = False

        # If we specify a script path, then we'll load the script from disk
        # into memory, and encode it for the server.
        # On setup script is called by the server for the first tick and only
        # the first script
        self.setup_script = setup_script
        self.tick_script = tick_script

    # Turn this node into a packet that the server can view
    def serialize(self):
        bencode = lambda x: base64.b64encode(x.encode("utf8")).decode()
        return "<NODE>{} {} {} {} {} {} {} {}".format(
            self.node_id,
            self.x, self.y, self.z,
            self.texture_name,
            bencode(self.setup_script) if not self.setup_script is None else "cGFzcw==",
            bencode(self.tick_script) if not self.tick_script is None else "cGFzcw==",
            base64.b64encode(' '.join([str(i) for i in self.metadata]).encode("utf8")).decode()
        )


