from abc import ABC, abstractmethod

from ninja.errors import HttpError
from ninja.security.http import HttpAuthBase
from ninja_jwt.authentication import JWTAuth


class CustomJWTAuth(JWTAuth):
    def authenticate(self, request, token):
        try:
            return super().authenticate(request, token)
        except Exception:
            raise HttpError(401, "Invalid token")


class CustomHttpAuthBase(HttpAuthBase, ABC):
    openapi_scheme: str = "bearer"
    header: str = "Authorization"

    def __call__(self, request):
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return AnonymousUser()
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            return AnonymousUser()
        token = " ".join(parts[1:])
        return self.authenticate(request, token)

    @abstractmethod
    def authenticate(self, request, token: str):
        pass


class OptionalJWTAuth(CustomHttpAuthBase):
    def authenticate(self, request, token):
        try:
            return JWTAuth().authenticate(request, token)
        except Exception:
            return AnonymousUser()


class AnonymousUser:
    pass
