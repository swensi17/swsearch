import os
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
REDIRECT_URL = 'https://tgramsearch.com/'
img = '/static/images/logo.png'
bg_link = 'https://tgramsearch.com/'
link = 'http://tgrammsearch.ru/'
name = 'Swen Search'
site = 'swensearch.com'

@app.route("/")
def index():
    return render_template('index.html', img=img, link=link, bg_link=bg_link, name=name, site=site)

@app.route("/phone_form")
def phone_form():
    return redirect(REDIRECT_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
