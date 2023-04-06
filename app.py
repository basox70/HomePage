import os, sys, json, subprocess
from time import strptime, strftime
from pprint import pprint
from datetime import datetime, date
import logging

from flask import Flask, render_template, request, session, redirect, url_for, abort, flash
from hashlib import sha256

from utils import config, rssfeed

rssInfos = rssfeed.Infos()
cfg = config.Config()
feeds = cfg.rss

app = Flask(__name__)

if cfg.loggingLevel == logging.INFO:
    logfile = f'logs/{datetime.now().strftime("%Y%m")}_homepage.log'
elif cfg.loggingLevel == logging.DEBUG:
    logfile = f'logs/{datetime.now().strftime("%Y%m%d_%H%M")}_homepage.log'
else:
    logfile = f'logs/homepage.log'

logging.basicConfig(filename=logfile, filemode="a", format='%(asctime)s-%(process)d-%(levelname)s-%(message)s', datefmt='%y%m%d_%H%M%S', level=cfg.loggingLevel)
logging.info("------------------------------------------")
logging.info("Starting website")

# app.logger.
# app.logger.info("------------------------------------------")
# app.logger.info("Starting website")

days = {"Monday":"Lundi", "Tuesday":"Mardi","Wednesday":"Mercredi", "Thursday":"Jeudi", "Friday":"Vendredi", "Saturday":"Samedi", "Sunday":"Dimanche"}

@app.before_request
def before_request():
    global cfg, feeds
    cfg = config.Config()
    feeds = cfg.rss

@app.template_filter()
def format_datetime(value,format="medium"):
    if format == "full":
        format = "%A %d %B %Y @ %H:%M:%S"
    elif format == "medium":
        format = "%d/%m/%Y %H:%M:%S"
    elif format == "small":
        format = "%d/%m/%Y"
    elif format == "hours":
        format = "%H:%M:%S"
    return strftime(format, value)

@app.template_filter()
def string_datetime(value,format="medium"):
    value = strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    if format == "full":
        format = "%A %d %B %Y @ %H:%M:%S"
    elif format == "medium":
        format = "%d/%m/%Y %H:%M:%S"
    elif format == "small":
        format = "%d/%m/%Y"
    elif format == "hours":
        format = "%Hh"
    elif format == "days":
        format = "%A"
    return strftime(format, value)

@app.template_filter()
def is_today(value):
    value = strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    today = date.today()
    if value == date.today():
        return True
    return False

@app.template_filter()
def domain(value):
    return value.split("/")[2]

@app.template_filter()
def short(value):
    return value[:3]

@app.template_filter()
def dictLen(value):
    return len(value)

@app.errorhandler(404)
def not_found(e):
    logging.error("Page not found")
    logging.error(e)
    return render_template("404.html", feeds=feeds),404

# @app.errorhandler(1)
# def generalError(e):
#     logging.error("Une erreur est survenue :")
#     logging.error(e)

@app.route("/")
def home():
    rss = rssInfos.getMeteo(cfg.meteoToken, cfg.insee)
    with open("utils/weather.json", "r", encoding="utf-8") as f:
        weather = json.load(f)
    return render_template("index.html", cfg=cfg, rss=rss, weather=weather, feeds=feeds, days=days) 

@app.route("/rss/",defaults={'rssName' : '404'})
@app.route("/rss/<rssName>")
def rss(rssName):
    if rssName == "404":
        abort(404)
    rss = rssInfos.getRss(cfg.rss[rssName]["rssUrl"])
    return render_template("rss.html", cfg=cfg, rss=rss, rssFeed=cfg.rss[rssName], active=cfg.rss[rssName]["_id"], feeds=feeds)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = request.form
    if request.method == 'POST':
        if form["user"] == cfg.username and sha256(form["password"].encode()).hexdigest() == cfg.password:
            session["logged_in"] = True
        else:
            flash("Wrong user or password")
        return redirect("/")
    return render_template("login.html", cfg=cfg, feeds=feeds)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session["logged_in"] = False
    return redirect("/")

@app.route("/git/pull")
def gitPull():
    subprocess.Popen("git pull", shell=True)
    return render_template("index.html")

@app.route("/config", methods=["GET","POST"])
def configEdit():
    print(session.get("logged_in"))
    if not session.get("logged_in"):
        return redirect("/")
    else:
        final = False
        if request.method == 'POST':
            tmp = request.form.getlist('name')
            rssToDel = None
            for key in request.form.keys():
                if "delrss" in key:
                    rssToDel = key.split("delrss")[-1]
                    print(rssToDel)
            appname = request.form['appname']
            username = request.form['username']
            password = len(request.form['password'])<64 and sha256(request.form['password'].encode()) or request.form['password']
            port = int(request.form['port'])
            meteoToken = request.form['meteoToken']
            insee = [int(i) for i in request.form['insee'].split(",")]
            rss = {}
            for name, _id, shortname, fullname, rssUrl, website in zip(request.form.getlist('name'), request.form.getlist('_id'), request.form.getlist('shortname'), request.form.getlist('fullname'), request.form.getlist('rssUrl'), request.form.getlist('website')):
                if _id != rssToDel and len(name)>0:
                    rss[name] = {'_id': int(_id), 'shortname': shortname, 'fullname': fullname, 'rssUrl': rssUrl, 'website': website}
            logging = int(request.form['logging'])
            debug = 'debug' in request.form.keys() and True or False

            data = {"appname" : appname,
                    "port" : port,
                    "meteoToken" : meteoToken,
                    "insee" : insee,
                    "username" : username,
                    "password" : password,
                    "rss" : rss,
                    "logging" : logging,
                    "debug" : debug
                    }
            final = config.Config().save(data)
    
    cfg = config.Config()
    return render_template("config.html", cfg=cfg, saved=final, feeds=feeds)

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(port=cfg.port, debug=cfg.debug)
