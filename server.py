import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for, abort


class DataManager:
    def __init__(self):
        self.json_clubs_path = "clubs.json"
        self.json_comp_path = "competitions.json"
        self._clubs = []
        self._competitions = []
        self.load_all_data()  # Charger les données au démarrage

    def _load_data_from_file(self, json_path, key):
        with open(json_path, "r") as json_file:
            return json.load(json_file).get(key, [])

    def load_all_data(self):
        """Charge toutes les données (clubs et compétitions) depuis les fichiers."""
        self._clubs = self._load_data_from_file(self.json_clubs_path, "clubs")
        self._clubs = sorted(self._clubs, key=lambda club: club["name"])

        self._competitions = self._load_data_from_file(
            self.json_comp_path, "competitions"
        )

    def get_clubs(self):
        return self._clubs

    def get_competitions(self):
        return self._competitions

    def save_clubs(self):
        """Sauvegarde les clubs dans leur fichier JSON."""
        with open(self.json_clubs_path, "w") as f:
            json.dump({"clubs": self._clubs}, f, indent=4)

    def save_competitions(self):
        """Sauvegarde les compétitions dans leur fichier JSON."""
        with open(self.json_comp_path, "w") as f:
            json.dump({"competitions": self._competitions}, f, indent=4)


data_manager = DataManager()
clubs = data_manager.get_clubs()
competitions = data_manager.get_competitions()


def purchase_validation(competition, club, placesRequired, competition_date):
    if placesRequired > int(club["points"]) or int(club["points"]) <= 0:
        print("not enough points")
        return False, "Not enough points"

    elif placesRequired > 12:
        print("places required > 12")
        return False, "Impossible to purchase more than 12 places"

    elif int(competition["numberOfPlaces"]) < placesRequired:
        print("not enough places")
        return False, "Not enough places available"

    elif competition_date < now:
        print("past competition")
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
                            print("already 12 places booked")
                            return (
                                False,
                                "You already have 12 places booked, you can't purchase more places.",
                            )
                        else:
                            print("impossible")
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
    print("toto")

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
        # Commenter ces deux lignes avant d'exécuter locust
        # data_manager.save_competitions()
        # data_manager.save_clubs()

        flash(
            f"Booking {placesRequired} place(s) for '{competition['name']}' complete!"
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
