from flask import Flask
from SpaceEye import SpaceEye
from api import api

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev'
)

app.register_blueprint(SpaceEye)
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True)