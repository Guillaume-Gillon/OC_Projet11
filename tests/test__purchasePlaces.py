import pytest
from datetime import datetime, timedelta
import server


@pytest.fixture
def mock_data():

    now = datetime.now()
    date_competition = now + timedelta(days=1)
    formatted_date_competition = date_competition.strftime("%Y-%m-%d %H:%M:%S")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            server,
            "clubs",
            [{"name": "Simply Lift", "email": "john@simplylift.co", "points": "5"}],
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


def post_data(competition, club, places):
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
    competition, club = get_competition_and_club_names()
    response = post_data(competition, club, number_required_places)

    assert response.status_code == 403


def test_enough_points(mock_data):

    number_required_places = int(server.clubs[0]["points"]) - 1
    competition, club = get_competition_and_club_names()
    response = post_data(competition, club, number_required_places)

    assert response.status_code == 200


def test_should_decrease_available_places(mock_data):

    initial_number_of_places = int(server.competitions[0]["numberOfPlaces"])
    competition, club = get_competition_and_club_names()
    post_data(competition, club, 5)

    assert int(server.competitions[0]["numberOfPlaces"]) == initial_number_of_places - 5


def test_zero_points_available(mock_data):

    club_points = int(server.clubs[0]["points"])
    server.clubs[0]["points"] = club_points - club_points

    competition, club = get_competition_and_club_names()
    response = post_data(competition, club, 1)

    assert response.status_code == 403


def test_purchase_more_than_twelve(mock_data):

    competition, club = get_competition_and_club_names()
    response = post_data(competition, club, 13)

    assert response.status_code == 403


def test_booking_places_in_past_competition(mock_data):

    server.competitions[0]["date"] = "2020-10-22 13:30:00"
    competition, club = get_competition_and_club_names()
    response = post_data(competition, club, 1)

    assert response.status_code == 403
