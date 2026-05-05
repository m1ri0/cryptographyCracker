from .models import PasswordModel

class PasswordMapper:
    @staticmethod
    def to_dict(password_model: PasswordModel) -> dict:
        return {
            "id": password_model.id,
            "password": password_model.password,
            "hash": password_model.hashed_password,
            "status": password_model.status
        }