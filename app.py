from flask import Flask, redirect, url_for, session,render_template
from pymongo import MongoClient

from auth import auth_bp
from property import property_bp

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'

client = MongoClient("mongodb+srv://user:user@cluster0.u3fdtma.mongodb.net/calisto_flask1")
db = client['calisto_flask1']
app.config['db'] = db

app.register_blueprint(auth_bp)
app.register_blueprint(property_bp)

# @app.route('/')
# def index():
#     return redirect(url_for('property.list_properties'))

@app.route('/')
def index():
    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True)
