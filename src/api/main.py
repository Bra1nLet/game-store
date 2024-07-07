# main.py
from flask import Flask, jsonify
from blueprints.basic_enpoints import blueprint as basic_enpoints

app = Flask(__name__)
app.register_blueprint(basic_enpoints)

if __name__ == '__main__':
    app.run()
