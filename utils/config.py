import os, sys, json
from hashlib import sha256

class Config(object):
    def __init__(self):
        if not os.path.isfile("config.json"):
            sys.exit("'config.json' not found! Please add it and try again.")
        else:
            with open("config.json") as file:
                config = json.load(file)

        for k in config:
            setattr(self, k, config[k])
            if k == "password" and len(config[k])<64:
                setattr(self, k, sha256(config[k].encode()).hexdigest())
        
    def save(self, cfg):
        with open("config.json","w") as f:
            json.dump(cfg, f,indent=4)
            return True
        return False
        