from flask import Blueprint, render_template, redirect

SpaceEye = Blueprint('SpaceEye', __name__)

@SpaceEye.route("/SpaceEye")
def homepage():
    return render_template(
        "SpaceEye.html"
    )

@SpaceEye.route("/add")
def add():
    return redirect("SpaceEye")
