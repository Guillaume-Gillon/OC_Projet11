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


def purchase_validation(competition, club, placesRequired, competition_date):
    if placesRequired > int(club["points"]) or int(club["points"]) <= 0:
        return False, "Not enough points"

    elif placesRequired > 12:
        return False, "Impossible to purchase more than 12 places"

    elif int(competition["numberOfPlaces"]) < placesRequired:
        return False, "Not enough places available"

    elif competition_date < now:
        return False, "Impossible to purchase places of an ended competition"

    else:
        if "booking" not in club:
            return True, ""
        else:
            booking_exists_for_this_competition = False
            for booked_places in club["booking"]:
                if booked_places["competition_name"] == competition["name"]:
                    booking_exists_for_this_competition = True
                    if (
                        int(booked_places["numberOfBookedPlaces"]) + int(placesRequired)
                        > 12
                    ):
                        possible_purchase = 12 - int(
                            booked_places["numberOfBookedPlaces"]
                        )
                        if possible_purchase <= 0:
                            return (
                                False,
                                "You already have 12 places booked, you can't purchase more places.",
                            )
                        else:
                            return (
                                False,
                                f"You can't purchase more than {possible_purchase} place(s)",
                            )
                    return True, ""

            if not booking_exists_for_this_competition:
                return True, ""

    return True, ""


app = Flask(__name__)
app.secret_key = "something_special"

competitions = loadCompetitions()
clubs = loadClubs()

competitions_db = "competitions.json"
clubs_db = "clubs.json"

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
        booking_possibility = 12
        if "booking" in foundClub:
            for booked_places in foundClub["booking"]:
                if booked_places["competition_name"] == foundCompetition["name"]:
                    booking_possibility = 12 - int(
                        booked_places["numberOfBookedPlaces"]
                    )
                    break
        return render_template(
            "booking.html",
            club=foundClub,
            competition=foundCompetition,
            booking_possibility=booking_possibility,
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

    validation, description = purchase_validation(
        competition, club, placesRequired, competition_date
    )

    if not validation:
        abort(403, description=description)

    else:
        competition["numberOfPlaces"] = str(
            int(competition["numberOfPlaces"]) - placesRequired
        )
        club["points"] = str(int(club["points"]) - placesRequired)

        if "booking" not in club:
            club["booking"] = [
                {
                    "competition_name": competition["name"],
                    "numberOfBookedPlaces": str(placesRequired),
                }
            ]
        else:
            for booked_place_entry in club["booking"]:
                if booked_place_entry["competition_name"] == competition["name"]:
                    current_booked = int(booked_place_entry["numberOfBookedPlaces"])
                    total_after_purchase = current_booked + placesRequired
                    booked_place_entry["numberOfBookedPlaces"] = str(
                        total_after_purchase
                    )
                    break

        competitions_data = {"competitions": competitions}
        clubs_data = {"clubs": clubs}

        with open(competitions_db, "w") as comp_file:
            json.dump(competitions_data, comp_file, indent=4)

        with open(clubs_db, "w") as clubs_file:
            json.dump(clubs_data, clubs_file, indent=4)

        flash(
            f"Booking {placesRequired} place(s) for '{competition['name']}' complete! ({club["points"]} points available now)"
        )
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
