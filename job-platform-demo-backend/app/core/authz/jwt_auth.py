from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError


class CustomJWTAuth(JWTAuth):
    def authenticate(self, request, token):
        try:
            return super().authenticate(request, token)
        except Exception:
            raise HttpError(401, "Invalid token")
