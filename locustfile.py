from locust import HttpUser, task, between
import random
import time


class WebsiteUser(HttpUser):
    """
    Simule un utilisateur de l'application Flask.
    """

    wait_time = between(1, 5)
    host = "http://127.0.0.1:5000"

    # Données des compétitions et clubs simulées
    SAMPLE_COMPETITIONS = [
        {
            "name": "Spring Festival",
            "date": "2026-03-27 10:00:00",
        },
        {
            "name": "Fall Classic",
            "date": "2026-10-22 13:30:00",
        },
    ]

    SAMPLE_CLUBS = [
        {"name": "Iron Temple", "email": "admin@irontemple.com"},
        {"name": "She Lifts", "email": "kate@shelifts.co.uk"},
        {"name": "Simply Lift", "email": "john@simplylift.co"},
    ]

    def on_start(self):
        """
        Appelée quand un utilisateur commence sa session.
        Simule la visite de la page d'accueil et authentifie l'utilisateur.
        """

        self.selected_club = random.choice(self.SAMPLE_CLUBS)
        email = self.selected_club["email"]
        self.current_user_email = email

        self.client.get("/", name="Visit homepage")
        self.client.post("/showSummary", data={"email": email}, name="Login")

    @task(3)  # Probabilité moyenne d'explorer les clubs
    def list_clubs(self):
        """
        Simule la visite de la page listant tous les clubs.
        """
        self.client.get("/clubs", name="List clubs")

    @task(5)  # Haute probabilité de tenter une réservation après connexion
    def book_and_purchase(self):
        """
        Simule le flux de réservation et d'achat de places.
        """

        selected_competition = random.choice(self.SAMPLE_COMPETITIONS)

        # 1. Accéder à la page de réservation
        self.client.get(
            f"/book/{selected_competition['name']}/{self.selected_club['name']}",
            name="/book/[competition]/[club]",
        )

        # 2. Acheter des places
        places_to_purchase = 1
        self.client.post(
            "/purchasePlaces",
            data={
                "competition": selected_competition["name"],
                "club": self.selected_club["name"],
                "places": str(places_to_purchase),
            },
            name="Purchase places",
        )

    @task(1)  # Faible probabilité de se déconnecter avant toute autre action
    def logout(self):
        self.client.get("/logout", name="Logout")
        if hasattr(self, "current_user_email"):
            del self.current_user_email

        # Une fois déconnecté, l'utilisateur n'exécute plus que la tâche idle_forever
        self.tasks = [self.idle_forever]

    def idle_forever(self, user):
        time.sleep(3600)
