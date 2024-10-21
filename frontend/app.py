from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template(
        "SpaceEye.html"
    )

@app.route("/add")
def add():
    return redirect("SpaceEye")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
