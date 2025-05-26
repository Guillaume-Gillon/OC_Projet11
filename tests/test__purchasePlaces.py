import pytest
from datetime import datetime, timedelta
import server


@pytest.fixture
def mock_data(monkeypatch, tmp_path):
    # Assure que la date de la competition est toujours postérieure à la date actuelle
    now = datetime.now()
    date_competition = now + timedelta(days=1)
    formatted_date_competition = date_competition.strftime("%Y-%m-%d %H:%M:%S")

    # Remplace le chemin des fichiers json pour écrire dans un fichier temporaire
    competitions_db = tmp_path / "competitions_tmp.json"
    clubs_db = tmp_path / "clubs_tmp.json"
    monkeypatch.setattr(server, "competitions_db", competitions_db)
    monkeypatch.setattr(server, "clubs_db", clubs_db)

    # Adapte les données extraites des fichiers json originaux
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            server,
            "clubs",
            [
                {
                    "name": "Simply Lift",
                    "email": "john@simplylift.co",
                    "points": "5",
                    "booking": [
                        {
                            "competition_name": "Spring Festival",
                            "numberOfBookedPlaces": "0",
                        }
                    ],
                }
            ],
        )
        monkeypatch.setattr(
            server,
            "competitions",
            [
                {
                    "name": "Spring Festival",
                    "date": formatted_date_competition,
                    "numberOfPlaces": "100",
                }
            ],
        )
        yield


def get_competition_and_club_names():
    return server.competitions[0]["name"], server.clubs[0]["name"]


def post_data(places):
    competition, club = get_competition_and_club_names()
    response = server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": competition,
            "club": club,
            "places": places,
        },
    )
    return response


def test_not_enough_points(mock_data):
    number_required_places = int(server.clubs[0]["points"]) + 1
    response = post_data(number_required_places)
    assert response.status_code == 403


def test_enough_points(mock_data):
    number_required_places = int(server.clubs[0]["points"]) - 1
    assert post_data(number_required_places).status_code == 200


def test_should_decrease_available_places(mock_data):
    initial_number_of_places = int(server.competitions[0]["numberOfPlaces"])
    post_data(5)
    assert int(server.competitions[0]["numberOfPlaces"]) == initial_number_of_places - 5


def test_zero_points_available(mock_data):
    club_points = int(server.clubs[0]["points"])
    server.clubs[0]["points"] = club_points - club_points
    assert post_data(1).status_code == 403


def test_purchase_more_than_twelve(mock_data):
    assert post_data(13).status_code == 403


def test_more_than_twelve_with_ten_already_booked(mock_data):
    booked_places_entry = server.clubs[0]["booking"][0]
    booked_places_entry["numberOfBookedPlaces"] = 10
    purchased_places = 3
    assert post_data(purchased_places).status_code == 403


def test_less_than_twelve_with_ten_already_booked(mock_data):
    booked_places_entry = server.clubs[0]["booking"][0]
    booked_places_entry["numberOfBookedPlaces"] = 10
    purchased_places = 1
    assert post_data(purchased_places).status_code == 200


def test_booking_places_in_past_competition(mock_data):
    server.competitions[0]["date"] = "2020-10-22 13:30:00"
    assert post_data(1).status_code == 403


def test_should_decrease_available_points(mock_data):
    points_before_purchase = int(server.clubs[0]["points"])
    purchased_places = 1
    post_data(purchased_places)
    assert int(server.clubs[0]["points"]) == points_before_purchase - purchased_places


def test_not_enough_places_available(mock_data):
    server.competitions[0]["numberOfPlaces"] = 1
    assert post_data(2).status_code == 403
