from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model


def create_jwt(user):
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user.pk,
        "email": user.email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_user_from_request(request):
    token = request.COOKIES.get("jwt")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    User = get_user_model()
    try:
        return User.objects.get(pk=payload.get("user_id"))
    except User.DoesNotExist:
        return None
