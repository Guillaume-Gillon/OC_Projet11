import pytest
from datetime import datetime, timedelta
import server


@pytest.fixture
def mock_data(monkeypatch, mocker):
    mock_manager = mocker.Mock(spec=server.DataManager)
    monkeypatch.setattr(server, "data_manager", mock_manager)
    # Assure que la date de la competition est toujours postérieure à la date actuelle
    now = datetime.now()
    date_competition = now + timedelta(days=1)
    formatted_date_competition = date_competition.strftime("%Y-%m-%d %H:%M:%S")

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
        yield mock_manager


@pytest.fixture
def client_fixture():
    server.app.config["TESTING"] = True
    server.app.config["SECRET_KEY"] = "test_secret_key"
    with server.app.test_client() as client:
        yield client
