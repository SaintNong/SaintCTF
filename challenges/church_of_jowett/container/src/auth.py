import jwt
from flask import request, jsonify, current_app, make_response
from functools import wraps
import secrets

SECRET_KEY = "jowett_is_the_best"


def create_token(data):
    token = jwt.encode(data, SECRET_KEY, algorithm="HS256")
    return token


def token_value(token):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return decoded_token


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None


def is_pope_role():
    # if user isn't authed at all
    if "auth_token" not in request.cookies:
        return False
    token = request.cookies.get("auth_token")
    try:
        data = decode_token(token)
        if data.get("is_pope", False):
            return True
    except jwt.DecodeError:
        return False
    return False


def is_cardinal_role():
    # if user isn't authed at all
    if "auth_token" not in request.cookies:
        return False
    token = request.cookies.get("auth_token")
    try:
        data = decode_token(token)
        if data.get("is_cardinal", False):
            return True
    except jwt.DecodeError:
        return False
    return False


def is_authenticated():
    # if user isn't authed at all
    if "auth_token" not in request.cookies:
        return False

    token = request.cookies.get("auth_token")

    try:
        if jwt.decode(token, SECRET_KEY, algorithms=["HS256"]) is not None:
            return True
    except jwt.DecodeError:
        return False
    return False


def promote_token():
    token = request.cookies.get("auth_token")
    data = decode_token(token)
    try:
        data["is_cardinal"] = True
        token = create_token(data)
        return token
    except jwt.DecodeError:
        return token
    return token


def requires_cardinal(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("auth_token")
        if not token:
            return (
                jsonify(
                    {
                        "message": "Token is missing, you must be logged in to access this"
                    }
                ),
                401,
            )
        try:
            data = decode_token(token)
            if data is None or data.get("is_cardinal") is None:
                return jsonify({"message": "Invalid token, you're not a cardinal"}), 401
            if data["is_cardinal"]:
                request.user_data = data
            else:
                return jsonify({"message": "Invalid token, data is wrong"}), 401
        except jwt.DecodeError:
            return jsonify({"message": "Invalid token, data is wrong"}), 401

        return f(*args, **kwargs)

    return decorated


def requires_pope(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("auth_token")
        if not token:
            return (
                jsonify(
                    {
                        "message": "Token is missing, you must be logged in to access this"
                    }
                ),
                401,
            )
        try:
            data = decode_token(token)
            if data is None or data.get("is_pope") is None:
                return jsonify({"message": "Invalid token, you're not the Pope"}), 401
            if data["is_pope"]:
                request.user_data = data
            else:
                return jsonify({"message": "Invalid token, data is wrong"}), 401
        except jwt.DecodeError:
            return jsonify({"message": "Invalid token, data is wrong"}), 401

        return f(*args, **kwargs)

    return decorated


def requires_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("auth_token")
        if not token:
            return (
                jsonify(
                    {
                        "message": "Token is missing, you must be logged in to access this"
                    }
                ),
                401,
            )

        try:
            data = decode_token(token)
            if data is None:
                return jsonify({"message": "Invalid token, data is wrong"}), 401
            request.user_data = data
        except jwt.DecodeError:
            return jsonify({"message": "Invalid token, data is wrong"}), 401

        return f(*args, **kwargs)

    return decorated
