import pytest
import server


@pytest.fixture
def mock_data():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            server,
            "clubs",
            [{"name": "Simply Lift", "email": "john@simplylift.co", "points": "13"}],
        )
        monkeypatch.setattr(
            server,
            "competitions",
            [{"name": "Spring Festival", "numberOfPlaces": "25"}],
        )
        yield


def test_not_enough_points(mock_data):

    number_required_places = int(server.clubs[0]["points"]) + 1

    response = server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": number_required_places,
        },
    )
    assert response.status_code == 403


def test_enough_points(mock_data):

    number_required_places = int(server.clubs[0]["points"]) - 1

    response = server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": number_required_places,
        },
    )
    assert response.status_code == 200


def test_should_decrease_available_places(mock_data):

    initial_number_of_places = int(server.competitions[0]["numberOfPlaces"])

    server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": 5,
        },
    )
    assert int(server.competitions[0]["numberOfPlaces"]) == initial_number_of_places - 5


def test_zero_points_available(mock_data):

    server.clubs[0]["points"] = int(server.clubs[0]["points"]) - int(
        server.clubs[0]["points"]
    )

    response = server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": 1,
        },
    )

    assert response.status_code == 403


def test_purchase_more_than_twelve(mock_data):

    response = server.app.test_client().post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": 13,
        },
    )

    assert response.status_code == 403
