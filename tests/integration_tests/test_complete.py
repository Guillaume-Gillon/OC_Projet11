import pytest
from pathlib import Path
import server


@pytest.fixture
def initial_data_context(mock_data, tmp_path):
    """
    Données initiales
    """
    mock_data.json_clubs_path = tmp_path / "clubs_tmp.json"
    mock_data.json_comp_path = tmp_path / "competitions_tmp.json"
    temp_clubs_file_path = Path(mock_data.json_clubs_path)
    temp_competitions_file_path = Path(mock_data.json_comp_path)

    real_data_manager = server.DataManager()
    real_data_manager.json_clubs_path = str(temp_clubs_file_path)
    real_data_manager.json_comp_path = str(temp_competitions_file_path)
    mock_data.save_clubs.side_effect = real_data_manager.save_clubs
    mock_data.save_competitions.side_effect = real_data_manager.save_competitions
    return {
        "temp_clubs_file_path": temp_clubs_file_path,
        "temp_competitions_file_path": temp_competitions_file_path,
    }


@pytest.fixture
def logged_in_client(mock_data, client_fixture):
    """
    Fixture qui connecte un client et le retourne.
    """
    login_response = client_fixture.post(
        "/showSummary", data={"email": server.clubs[0]["email"]}, follow_redirects=True
    )
    assert login_response.status_code == 200
    assert server.clubs[0]["email"].encode() in login_response.data

    yield client_fixture  # Retourne le client avec un utilisateur connecté


@pytest.mark.integration
def test_login(mock_data, client_fixture):
    login_response = client_fixture.post(
        "/showSummary", data={"email": server.clubs[0]["email"]}, follow_redirects=True
    )
    assert login_response.status_code == 200
    assert server.clubs[0]["email"].encode() in login_response.data
    assert b"Welcome" in login_response.data
    mock_data.save_clubs.assert_not_called()
    mock_data.save_competitions.assert_not_called()


@pytest.mark.integration
def test_logout(mock_data, logged_in_client):
    logout_response = logged_in_client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert server.clubs[0]["email"].encode() not in logout_response.data
    mock_data.save_clubs.assert_not_called()
    mock_data.save_competitions.assert_not_called()


@pytest.mark.integration
def test_load_booking_page(mock_data, logged_in_client):
    comp_name = server.competitions[0]["name"]
    club_name = server.clubs[0]["name"]
    places_available = server.competitions[0]["numberOfPlaces"]

    booking_page_response = logged_in_client.get(
        f"/book/{comp_name}/{club_name}",
        follow_redirects=True,
    )
    assert booking_page_response.status_code == 200
    assert f"Booking for {comp_name}".encode() in booking_page_response.data
    assert (
        f"Places available: {places_available}".encode() in booking_page_response.data
    )
    assert b'<select name="places" id="places">' in booking_page_response.data
    assert b'<button type="submit">Book</button>' in booking_page_response.data

    mock_data.save_clubs.assert_not_called()
    mock_data.save_competitions.assert_not_called()


@pytest.mark.integration
def test_purchase_places(mock_data, client_fixture):
    places_to_purchase = 1
    purchase_response = client_fixture.post(
        "/purchasePlaces",
        data={
            "competition": server.competitions[0]["name"],
            "club": server.clubs[0]["name"],
            "places": places_to_purchase,
        },
        follow_redirects=True,
    )

    assert purchase_response.status_code == 200
    assert (
        f"Booking {places_to_purchase} place(s) for &#39;{server.competitions[0]["name"]}&#39; complete!".encode()
        in purchase_response.data
    )
    mock_data.save_clubs.assert_called_once()
    mock_data.save_competitions.assert_called_once()


@pytest.mark.integration
def test_club_points_display(client_fixture):
    club_points_board = client_fixture.get("/clubs")
    assert club_points_board.status_code == 200
    assert b"List of clubs and points available" in club_points_board.data


@pytest.mark.integration
def test_full_purchase_flow(mock_data, client_fixture, initial_data_context):
    """
    Teste le flux complet : login, achat de places, puis logout.
    """

    club_name = server.clubs[0]["name"]  # Mock : "Simply Lift"
    comp_name = server.competitions[0]["name"]  # Mock : "Spring Festival"
    places_to_purchase = 1
    initial_club_points = int(server.clubs[0]["points"])  # Mock : 5
    initial_comp_places = int(server.competitions[0]["numberOfPlaces"])  # Mock : 100

    # --- Étape 1: Login ---
    login_response = client_fixture.post(
        "/showSummary", data={"email": "john@simplylift.co"}, follow_redirects=True
    )
    assert login_response.status_code == 200
    assert b"Welcome" in login_response.data
    # Vérifier que l'email du club est affiché
    assert b"john@simplylift.co" in login_response.data

    # --- Étape 2: Achat de places ---
    purchase_response = client_fixture.post(
        "/purchasePlaces",
        data={
            "competition": comp_name,
            "club": club_name,
            "places": str(places_to_purchase),
        },
        follow_redirects=True,
    )

    assert purchase_response.status_code == 200
    # purchase_response.data est de type bytes, donc on encode la f-string en bytes pour comparaison
    assert (
        f"Booking {places_to_purchase} place(s) for &#39;{comp_name}&#39; complete!".encode()
        in purchase_response.data
    )

    # Vérifications après l'achat
    assert int(server.clubs[0]["points"]) == initial_club_points - places_to_purchase
    assert (
        int(server.competitions[0]["numberOfPlaces"])
        == initial_comp_places - places_to_purchase
    )
    # Vérifier que les données ont été sauvegardées
    mock_data.save_clubs.assert_called_once()
    mock_data.save_competitions.assert_called_once()

    # Vérifier que les fichiers temporaires ont été créés
    assert initial_data_context["temp_clubs_file_path"].exists()
    assert initial_data_context["temp_competitions_file_path"].exists()

    # Réinitialiser les appels de sauvegardes
    mock_data.save_clubs.reset_mock()
    mock_data.save_competitions.reset_mock()

    # --- Étape 3: Logout ---
    logout_response = client_fixture.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    # Message de la page d'accueil
    assert b"Welcome to the GUDLFT Registration Portal!" in logout_response.data
    # L'email du club ne devrait plus être affiché après logout
    assert b"john@simplylift.co" not in logout_response.data

    # Vérifier qu'aucune sauvegarde n'a été effectuée pendant le logout
    mock_data.save_clubs.assert_not_called()
    mock_data.save_competitions.assert_not_called()
