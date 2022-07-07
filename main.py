
from flask import Flask, request, render_template
app = Flask(__name__)

@app.route("/")
def route():
    return '''<h1> hello world </h1>'''

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')