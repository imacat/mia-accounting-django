from mia_core.models import User


class AccountBackend:
    def get_partial_digest(self, username):
        if username != "imacat":
            return None
        return "5486b64881adaf7bc1485cc26e57e51e"

    def get_user(self, username):
        return User(username)
