import os, sys, json

class Config(object):
    def __init__(self):
        if not os.path.isfile("config.json"):
            sys.exit("'config.json' not found! Please add it and try again.")
        else:
            with open("config.json") as file:
                config = json.load(file)

        for k in config:
            setattr(self, k, config[k])
        
