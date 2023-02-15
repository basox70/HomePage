import json

from os import walk, mkdir, rename, remove
from os.path import isdir, join, getmtime, exists, getsize
from feedparser import parse
from contextlib import closing
from urllib.request import urlopen
from datetime import date, timedelta
from re import split as resplit
from pprint import pprint

class Infos():
    def __init__(self):
        # Create folder for weather data history, to avoid requests on refresh. API has limited call per day
        if not isdir("data"):
            try:
                mkdir("data")
            except OSError:
                print("Création du dossier échouée")
            else:
                print("Dossier data créé avec succès")
        if not isdir("data/oldData"):
            try:
                mkdir("data/oldData")
            except OSError:
                print("Création du dossier échouée")
            else:
                print("Dossier data/oldData créé avec succès")

    def getData(self, filename, url):
        """
        Get data from weather API and write into a file
        param :
            filename (str) : name of the file in which you write the json infos
            url (str) : url of the API with all infos needed (final url)
        return :
            json content of the request result
        """
        with open(filename,"w") as f:
            with closing(urlopen(url)) as u:
                data = json.loads(u.read())
                f.write(json.dumps(data,indent=2))
                return data

    def getCityFromInsee(self,insee):
        with closing(urlopen(f"https://geo.api.gouv.fr/communes?code={insee}")) as u:
            data = json.loads(u.read())
            if len(data) > 0:
                return data[0]["nom"]
            return "Unknown"

    def getRss(self,url):
        return parse(url)

    def getMeteo(self, token, insees):
        # date.fromtimestamp(getmtime(join("data",f)))
        for root, _, files in walk("data"):
            for file in files:
                fileDate = date.fromtimestamp(getmtime(join(root,file)))
                if fileDate < date.today() + timedelta(days=-730):
                    remove(join(root,file))

                if root == "data" and fileDate != date.today():
                    splitted = resplit("_|\.",file)
                    if not isdir(join(root,"oldData",splitted[1])):
                        mkdir(join(root,"oldData",splitted[1]))
                    rename(join(root,file),join(root,"oldData",splitted[1],f"{fileDate}_{splitted[0]}.{splitted[-1]}"))
                
        result = {}
        for insee in insees:
            files = [f"data/eph0_{insee}.json",f"data/eph1_{insee}.json",f"data/prevd_{insee}.json",f"data/prev_{insee}.json"]
            urls = [f'https://api.meteo-concept.com/api/ephemeride/0?token={token}&insee={insee}',
                    f'https://api.meteo-concept.com/api/ephemeride/1?token={token}&insee={insee}',
                    f'https://api.meteo-concept.com/api/forecast/daily/periods?token={token}&insee={insee}',
                    f'https://api.meteo-concept.com/api/forecast/daily?token={token}&insee={insee}']
            datas = [None,None,None,None]

            for i in range(0,4):
                if not exists(files[i]):
                    datas[i] = self.getData(files[i], urls[i])
                else:
                    if getsize(files[i]) == 0:
                        datas[i] = self.getData(files[i], urls[i])
                    else:
                        with open(files[i],"r") as f:
                            datas[i] = json.load(f)

            
            result[str(insee)] = {"eph0" : datas[0], "eph1" : datas[1], "prevd" : datas[2], "prev" : datas[3], "city" : self.getCityFromInsee(datas[2]["forecast"][0][0]["insee"])}
        return result
