from flask import (
    request,
    jsonify,
    Blueprint,
    current_app,
    make_response,
    render_template,
    redirect,
    url_for,
)
from src.auth import (
    decode_token,
    requires_pope,
    requires_token,
    is_authenticated,
    token_value,
    requires_cardinal,
    is_cardinal_role,
    is_pope_role,
    promote_token,
)
import random

api = Blueprint("api", __name__)


@api.route("/")
def index():
    if is_pope_role() and is_cardinal_role():
        return render_template(
            "public.html", is_auth=True, is_cardinal_role=True, is_pope_role=True
        )
    elif is_cardinal_role():
        return render_template("public.html", is_auth=True, is_cardinal_role=True)
    elif is_authenticated():
        return render_template("public.html", is_auth=True)
    return render_template("public.html")


@api.route("/signup", methods=("POST", "GET"))
def signup():

    # make sure user isn't authenticated
    if is_pope_role() and is_cardinal_role():
        return render_template(
            "public.html", is_auth=True, is_cardinal_role=True, is_pope_role=True
        )
    elif is_cardinal_role():
        return render_template("public.html", is_auth=True, is_cardinal_role=True)
    elif is_authenticated():
        return render_template("public.html", is_auth=True)

    # get form data
    if request.method == "POST":
        jwt_data = {}
        jwt_data["name"] = request.form.get("name")
        jwt_data["email"] = request.form.get("email")
        jwt_data["is_cardinal"] = False
        jwt_data["is_pope"] = False
        jwt_cookie = current_app.auth.create_token(jwt_data)
        if is_cardinal_role():
            response = make_response(
                redirect(
                    url_for(
                        "api.index",
                        is_auth=True,
                        is_cardinal_role=True,
                        is_pope_role=False,
                    )
                )
            )
        else:
            response = make_response(redirect(url_for("api.index", is_auth=True)))

        response.set_cookie("auth_token", jwt_cookie, httponly=True)
        return response

    return render_template("signup.html")


@api.route("/promote", methods=("GET", "POST"))
@requires_token
def promote():
    if is_pope_role() and is_cardinal_role():
        return render_template(
            "public.html", is_auth=True, is_cardinal_role=True, is_pope_role=True
        )
    elif is_cardinal_role():
        return render_template("public.html", is_auth=True, is_cardinal_role=True)
    elif request.method == "POST":
        jwt_cookie = promote_token()
        response = make_response(
            redirect(
                url_for(
                    "api.index", is_auth=True, is_cardinal_role=True, is_pope_role=False
                )
            )
        )
        response.set_cookie("auth_token", jwt_cookie, httponly=True)
        return response
    return render_template("promote.html")


@api.route("/cardinal_revelations", methods=("GET",))
@requires_cardinal
def cardinal_win():
    if is_pope_role() and is_cardinal_role():
        return render_template(
            "cardinal_revelations.html",
            flag="saint{h1s_h0lyness_w0uld_b3_pr0ud}",
            is_auth=True,
            is_cardinal_role=True,
            is_pope_role=True,
        )
    else:
        return render_template(
            "cardinal_revelations.html",
            flag="saint{h1s_h0lyness_w0uld_b3_pr0ud}",
            is_auth=True,
            is_cardinal_role=True,
        )


@api.route("/profile", methods=("GET",))
@requires_token
def info():
    data = decode_token(request.cookies.get("auth_token"))
    if is_pope_role() and is_cardinal_role():
        return render_template(
            "info.html",
            name=data["name"],
            email=data["email"],
            is_auth=True,
            is_cardinal_role=True,
            is_pope_role=True,
        )
    elif is_cardinal_role():
        return render_template(
            "info.html",
            name=data["name"],
            email=data["email"],
            is_auth=True,
            is_cardinal_role=True,
        )
    else:
        return render_template(
            "info.html", name=data["name"], email=data["email"], is_auth=True
        )


@api.route("/todo_list", methods=("GET",))
@requires_cardinal
def todo():
    if is_pope_role:
        return render_template(
            "todo.html",
            is_auth=True,
            is_cardinal_role=True,
            is_pope_role=True,
        )
    else:
        return render_template(
            "todo.html",
            is_auth=True,
            is_cardinal_role=True,
        )


@api.route("/pope_revelations", methods=("GET",))
@requires_pope
def pope_win():
    return render_template(
        "pope_revelations.html",
        flag="saint{j0w3tt_f0rg3ry?_th3r3_c4n_0n1y_b3_0n3!}",
        is_auth=True,
        is_cardinal_role=True,
        is_pope_role=True,
    )


@api.route("/logout")
def logout():
    response = make_response(redirect(url_for("api.index")))
    response.delete_cookie("auth_token")
    return response
