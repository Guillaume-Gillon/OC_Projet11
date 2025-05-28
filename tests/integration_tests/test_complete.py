import pytest
from pathlib import Path
import server


@pytest.fixture
def mock_tmp_files(mock_data, tmp_path):
    mock_data.json_clubs_path = tmp_path / "clubs_tmp.json"
    mock_data.json_comp_path = tmp_path / "competitions_tmp.json"


@pytest.mark.integration
def test_full_purchase_flow(client_fixture, mock_data, mock_tmp_files):
    """
    Teste le flux complet : login, achat de places, puis logout.
    """
    # Données initiales
    temp_clubs_file_path = Path(mock_data.json_clubs_path)
    temp_competitions_file_path = Path(mock_data.json_comp_path)

    real_data_manager = server.DataManager()
    real_data_manager.json_clubs_path = str(temp_clubs_file_path)
    real_data_manager.json_comp_path = str(temp_competitions_file_path)
    mock_data.save_clubs.side_effect = real_data_manager.save_clubs
    mock_data.save_competitions.side_effect = real_data_manager.save_competitions

    club_name = server.clubs[0]["name"]  # "Simply Lift"
    comp_name = server.competitions[0]["name"]  # "Spring Festival"
    places_to_purchase = 1
    initial_club_points = int(server.clubs[0]["points"])  # 5
    initial_comp_places = int(server.competitions[0]["numberOfPlaces"])  # 100

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
    assert temp_clubs_file_path.exists()
    assert temp_competitions_file_path.exists()

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
