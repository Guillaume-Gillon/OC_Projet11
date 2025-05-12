import server


def test_should_status_code_nok():

    response = server.app.test_client().post(
        "/showSummary", data={"email": "invalid@example.com"}
    )
    assert response.status_code == 404
