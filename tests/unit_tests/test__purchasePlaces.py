import pytest
import server


def post_data(client, places):
    competition = server.competitions[0]["name"]
    club = server.clubs[0]["name"]
    response = client.post(
        "/purchasePlaces",
        data={
            "competition": competition,
            "club": club,
            "places": places,
        },
    )
    return response


def check_data_saved(data):
    data.save_clubs.assert_called_once()
    data.save_competitions.assert_called_once()


def check_data_not_saved(data):
    data.save_clubs.assert_not_called()
    data.save_competitions.assert_not_called()


@pytest.mark.unit
def test_not_enough_points(client_fixture, mock_data):
    number_required_places = int(server.clubs[0]["points"]) + 1
    response = post_data(client_fixture, number_required_places)
    assert response.status_code == 403
    check_data_not_saved(mock_data)


@pytest.mark.unit
def test_enough_points(client_fixture, mock_data):
    number_required_places = int(server.clubs[0]["points"]) - 1
    assert post_data(client_fixture, number_required_places).status_code == 200
    check_data_saved(mock_data)


@pytest.mark.unit
def test_should_decrease_available_places(client_fixture, mock_data):
    initial_number_of_places = int(server.competitions[0]["numberOfPlaces"])
    post_data(client_fixture, 5)
    assert int(server.competitions[0]["numberOfPlaces"]) == initial_number_of_places - 5
    check_data_saved(mock_data)


@pytest.mark.unit
def test_zero_points_available(client_fixture, mock_data):
    club_points = int(server.clubs[0]["points"])
    server.clubs[0]["points"] = club_points - club_points
    assert post_data(client_fixture, 1).status_code == 403
    check_data_not_saved(mock_data)


@pytest.mark.unit
def test_purchase_more_than_twelve(client_fixture, mock_data):
    assert post_data(client_fixture, 13).status_code == 403
    check_data_not_saved(mock_data)


@pytest.mark.unit
def test_more_than_twelve_with_ten_already_booked(client_fixture, mock_data):
    booked_places_entry = server.clubs[0]["booking"][0]
    booked_places_entry["numberOfBookedPlaces"] = 10
    purchased_places = 3
    assert post_data(client_fixture, purchased_places).status_code == 403
    check_data_not_saved(mock_data)


@pytest.mark.unit
def test_less_than_twelve_with_ten_already_booked(client_fixture, mock_data):
    booked_places_entry = server.clubs[0]["booking"][0]
    booked_places_entry["numberOfBookedPlaces"] = 10
    purchased_places = 1
    assert post_data(client_fixture, purchased_places).status_code == 200
    check_data_saved(mock_data)


@pytest.mark.unit
def test_booking_places_in_past_competition(client_fixture, mock_data):
    server.competitions[0]["date"] = "2020-10-22 13:30:00"
    assert post_data(client_fixture, 1).status_code == 403
    check_data_not_saved(mock_data)


@pytest.mark.unit
def test_should_decrease_available_points(client_fixture, mock_data):
    points_before_purchase = int(server.clubs[0]["points"])
    purchased_places = 1
    post_data(client_fixture, purchased_places)
    assert int(server.clubs[0]["points"]) == points_before_purchase - purchased_places
    check_data_saved(mock_data)


@pytest.mark.unit
def test_not_enough_places_available(client_fixture, mock_data):
    server.competitions[0]["numberOfPlaces"] = 1
    assert post_data(client_fixture, 2).status_code == 403
    check_data_not_saved(mock_data)
