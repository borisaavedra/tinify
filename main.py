from flask import Flask, render_template, request, redirect, session, url_for
import requests
import json
import base64
import os
import pprint

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]


app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'


def get_token ():
    url_token = "https://accounts.spotify.com/api/token"

    p = { "grant_type":"client_credentials" }

    encoded = base64.b64encode(bytes(CLIENT_ID+":"+CLIENT_SECRET, "utf-8"))

    h = {"Authorization": f"Basic {str(encoded, 'utf-8')}" }
    
    try: 
        r = requests.post(url_token, data=p, headers=h)
        access_token = r.json()["access_token"]
        # print(r.json())
        return access_token
    except Exception as e:
        print("ERROR ACCESS TOKEN", e)
        return "Error access token: " + str(e)


def print_list(artists):
    for artist in artists:
        print(f"{artist['name']} {artist['popularity']} {artist['id']}", end="\n")


@app.route("/search", methods=["GET", "POST"])
def search():

    ep = "https://api.spotify.com/v1/search"

    access_token = get_token()

    if request.method == "POST":

        session.clear()

        headers = { "Authorization": f"Bearer {access_token}" }

        q = request.form["q"]
        q.replace(" ", "+")

        parameters = {
            "q": q,
            "type": "album,track,artist"
        }

        try:
            r = requests.get(ep, params=parameters, headers=headers)
        except Exception as e:
            print("Error getting data from API ", e)

        if r.status_code != 200:
            return "Fuck! " + str(r.status_code)
        else:

            artists = []
            albums = []
            tracks, date = [], []
            mydict = {}

            for item in r.json()["albums"]["items"]:
                mydict["artist_name"] = item["artists"][0]["name"]
                mydict["album_name"] = item["name"]
                date = str(item["release_date"]).split("-")
                mydict["album_release"] = date[0]
                mydict["total_tracks"] = item["total_tracks"]
                if len(item["images"]) > 0:
                    mydict["album_pic"] = item["images"][0]["url"]
                
                albums.append(mydict.copy())

            mydict.clear()

            for track in r.json()["tracks"]["items"]:
                mydict["album_name"] = track["album"]["name"]
                mydict["artist"] = track["album"]["artists"][0]["name"]
                mydict["track_preview"] = track["preview_url"]
                mm = track["duration_ms"] // 60000
                ss = track["duration_ms"] % 60000
                ss = list(str(ss))
                time = str(mm)+"' "+ss[0]+ss[0]+"''"
                mydict["track_duration"] = time
                mydict["track_name"] = track["name"]
                mydict["popularity"] = track["popularity"]

                tracks.append(mydict.copy())
            
            mydict.clear()

            for artist in r.json()["artists"]["items"]:
                mydict["name"] = artist["name"]
                mydict["popularity"] = artist["popularity"]
                mydict["id"] = artist["id"]
                if len(artist["images"]) > 0:
                    mydict["images"] = artist["images"][0]["url"]

                artists.append(mydict.copy())

            mydict.clear()

            # Sort list
            artists.sort(reverse=True, key=lambda artist: (artist["popularity"], artist["name"]))
            tracks.sort(reverse=True, key=lambda track: (track["popularity"], track["track_name"]))
            # session["artist"] = artists
            # session["albums"] = albums
            # session["tracks"] = tracks

            data = {
                "q": q,
                "artists": artists,
                "albums": albums,
                "tracks": tracks
            }

            return render_template("index.html", **data)
            # return redirect(url_for("index", q=q))
    else:
        return render_template("index.html")


@app.route("/", defaults={"q":None, "artists":None, "albums":None, "tracks":None})
# @app.route("/<q>")
def index(q, artists, albums, tracks):
    if q == None:
        return render_template("index.html")
    else:
        return render_template("index.html", q=q, artists=artists, albums=albums, tracks=tracks)
        # return render_template("index.html", artists=data["artists"], albums=data["albums"], tracks=data["tracks"])
        # return render_template("index.html", artists=session["artist"], tracks=session["tracks"], albums=session["albums"])