import os, sys, json
from time import strptime, strftime
from datetime import date
from pprint import pprint

from flask import Flask, render_template, request, session, redirect, url_for
import aiohttp

from utils import config, rssfeed

rssInfos = rssfeed.Infos()
cfg = config.Config()
app = Flask(cfg.appname)

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

@app.before_request
def before_request():
    cfg = config.Config() # in case of config change, reload the config

@app.route("/")
def home():
    feeds = cfg.rss
    rss = rssInfos.getMeteo(cfg.meteoToken, cfg.insee)
    with open("utils/weather.json", "r", encoding="utf-8") as f:
        weather = json.load(f)
    return render_template("index.html", rss = rss, weather = weather, feeds = feeds) 

@app.route("/rss/",defaults={'rssName' : '404'})
@app.route("/rss/<rssName>")
def rss(rssName):
    feeds = cfg.rss
    rss = rssInfos.getRss(cfg.rss[rssName]["rssUrl"])
    return render_template("rss.html", rss = rss, url=cfg.rss[rssName]["website"], title=cfg.rss[rssName]["fullname"], active=cfg.rss[rssName]["_id"], feeds =feeds)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
