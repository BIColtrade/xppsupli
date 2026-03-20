from .jwt_utils import get_user_from_request


def jwt_user(request):
    return {"jwt_user": get_user_from_request(request)}
