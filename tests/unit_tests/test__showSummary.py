import pytest


def post_data(client, email):
    return client.post("/showSummary", data={"email": email})


@pytest.mark.unit
def test_should_status_code_nok(mock_data, client_fixture):
    # Email présent dans les JSON originaux
    # La réussite de ce test prouve que des données simulées ont été utilisées
    assert post_data(client_fixture, "kate@shelifts.co.uk").status_code == 404


@pytest.mark.unit
def test_should_status_code_ok(mock_data, client_fixture):
    assert post_data(client_fixture, "john@simplylift.co").status_code == 200
