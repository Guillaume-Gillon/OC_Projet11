import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for, abort


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        sortedListOfClubs = sorted(listOfClubs, key=lambda club: club["name"])
        return sortedListOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        listOfCompetitions = json.load(comps)["competitions"]
        return listOfCompetitions


app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "something_special"

competitions = loadCompetitions()
clubs = loadClubs()

now = datetime.now()
strptime = datetime.strptime


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/showSummary", methods=["POST"])
def showSummary():
    matching_club = [club for club in clubs if club["email"] == request.form["email"]]
    if not matching_club:
        abort(404, description="Email not found.")
    else:
        club = matching_club[0]
        return render_template(
            "welcome.html",
            club=club,
            competitions=competitions,
            now=now,
            strptime=strptime,
        )


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club][0]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]
    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub, competition=foundCompetition
        )
    else:
        flash("Something went wrong-please try again")
        return render_template(
            "welcome.html",
            club=club,
            competitions=competitions,
            now=now,
            strptime=strptime,
        )


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    competition = [c for c in competitions if c["name"] == request.form["competition"]][
        0
    ]
    club = [c for c in clubs if c["name"] == request.form["club"]][0]
    placesRequired = int(request.form["places"])
    competition_date = datetime.strptime(competition["date"], "%Y-%m-%d %H:%M:%S")

    if placesRequired > int(club["points"]) or int(club["points"]) <= 0:
        abort(403, description="Not enough points")
        return render_template("welcome.html", club=club, competitions=competitions)

    elif placesRequired > 12:
        abort(403, description="Impossible to purchase more than 12 places")

    elif competition_date < now:
        abort(403, description="Impossible to purchase places of an ended competition")

    else:
        competition["numberOfPlaces"] = (
            int(competition["numberOfPlaces"]) - placesRequired
        )
        club["points"] = int(club["points"]) - placesRequired
        flash("Great-booking complete!")
        return render_template(
            "welcome.html",
            club=club,
            competitions=competitions,
            now=now,
            strptime=strptime,
        )


@app.route("/clubs")
def list_clubs():
    return render_template("clubs.html", clubs=clubs)


@app.route("/logout")
def logout():
    return redirect(url_for("index"))
