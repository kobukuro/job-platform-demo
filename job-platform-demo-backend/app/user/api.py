from django.utils import timezone
from django.db import transaction, IntegrityError
from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Response
from ninja_jwt.tokens import RefreshToken
from user.models import User
from user.schemas import UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse, \
    TokenRefreshRequest, TokenRefreshResponse

router = Router(tags=['User'])


@router.post("", response={201: UserRegistrationResponse})
def register_user(request, payload: UserRegistrationRequest) -> Response:
    """
        User registration API endpoint

        Args:
            request: HTTP request object
            payload (UserRegistrationRequest): Request data containing email and password

        Returns:
            Response: Returns 201 status code with newly created user data

        Raises:
            HttpError:
                - 409: When user with provided email already exists
                - 422: When validation fails
                - 500: For any other unexpected errors
    """
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=payload.email,
                password=payload.password
            )
            return Response(UserRegistrationResponse.from_orm(user).dict(), status=201)
    except IntegrityError as e:
        raise HttpError(409, "User with this email already exists")
    except Exception as e:
        raise HttpError(500, str(e))


@router.post("/login", response=UserLoginResponse)
def login_user(request, payload: UserLoginRequest) -> Response:
    """
    User login API endpoint

    Args:
        request: HTTP request object
        payload (UserLoginRequest): Request data containing email and password

    Returns:
        Response: Returns JWT tokens upon successful authentication

    Raises:
        HttpError:
            - 401: When credentials are invalid
            - 422: When validation fails
            - 500: For any other unexpected errors
    """
    try:
        user = User.objects.get(email=payload.email)
        if not user.check_password(payload.password):
            raise HttpError(401, "Invalid credentials")
        user.last_login = timezone.now()
        user.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        }, status=200)

    except HttpError:
        raise
    except User.DoesNotExist:
        raise HttpError(401, "Invalid credentials")
    except Exception as e:
        raise HttpError(500, str(e))


@router.post("/refresh_jwt", response=TokenRefreshResponse)
def refresh_token(request, payload: TokenRefreshRequest) -> Response:
    """
    Refresh token API endpoint

    Args:
        request: HTTP request object
        payload (TokenRefreshRequest): Request data containing refresh token

    Returns:
        Response: Returns new access token

    Raises:
        HttpError:
            - 401: When refresh token is invalid
            - 500: For any other unexpected errors
    """
    try:
        refresh = RefreshToken(payload.refresh_token)
        return Response({
            "access_token": str(refresh.access_token)
        }, status=200)

    except Exception as e:
        raise HttpError(401, "Invalid refresh token")
