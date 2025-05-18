from django.db import transaction, IntegrityError
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from user.models import User
from user.schemas import UserRegistrationRequest, UserRegistrationResponse

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
