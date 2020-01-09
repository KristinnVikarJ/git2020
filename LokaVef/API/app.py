import os
import requests
import datetime
import json
from time import *
import sqlite3 as lite
from flask import Flask, request
from flask_cors import CORS
from threading import Thread

API_URL = "https://api.scpslgame.com/lobbylist.php?format=json"

TotalPlayers = 0
TotalCapacity = 0
TotalServers = 0

con = lite.connect('database.db')
cur = con.cursor()
cur.execute('SELECT SQLITE_VERSION()')
data = cur.fetchone()

print("SQLite version: %s" % data)

cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='PlayerHistory'")

fetched = cur.fetchone()

if not fetched or len(fetched) == 0:
    # Table does not exist, lets create it
    cur.execute(
        "CREATE TABLE PlayerHistory(Count INT, Servers INT, Capacity INT, Time DATETIME)")


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/players')
    def players():
        return str(TotalPlayers)

    @app.route('/servers')
    def servers():
        return str(TotalServers)

    @app.route('/capacity')
    def capacity():
        return str(TotalCapacity)

    @app.route('/history')
    def history():
        con2 = lite.connect('database.db')
        amount = int(request.args.get('amount'))
        command = "SELECT * FROM PlayerHistory ORDER BY Time DESC LIMIT " + \
            str(amount)
        curs = con2.cursor()
        curs.execute(command)
        rows = curs.fetchall()
        items = []
        for row in rows:
            items.append(
                {"players": row[0], "servers": row[1], "capacity": row[2], "time": row[3]})
        return json.dumps(items)

    CORS(app)
    return app


def UpdateThread():
    global TotalPlayers
    global TotalCapacity
    global TotalServers
    while True:
        sleep(30)
        con = lite.connect('database.db')
        curs = con.cursor()
        r = requests.get(API_URL)
        TotalPlayers = 0
        TotalCapacity = 0
        TotalServers = 0
        for jsonObject in r.json():
            TotalPlayers += int(jsonObject['players'].rsplit("/", 1)[0])
            TotalCapacity += int(jsonObject['players'].rsplit("/", 1)[-1])
            TotalServers += 1
        print("Total Players Playing: " + str(TotalPlayers))
        print("Total Servers Online: " + str(TotalServers))
        time = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        curs.execute("INSERT INTO PlayerHistory VALUES(" + str(TotalPlayers) + "," + str(TotalServers) + "," + str(TotalCapacity) +
                     ",'" + time + "')")
        con.commit()


thread = Thread(target=UpdateThread)
thread.start()
