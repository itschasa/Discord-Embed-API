from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory, request
import json
import flask_limiter
import flask
import os
import base64
import time

browsers = ['chrome', 'windows', 'firefox']

# local imports
import utils, _config
from database import DataBase

template_dir = os.path.abspath(f'{os.getcwd()}/pages/')
app = Flask(__name__, template_folder=template_dir)
limiter = flask_limiter.Limiter(
    app,
    key_func=utils.returnIP,
    default_limits=["3 per second", "90 per minute"],
)

def parse_embed(data) -> dict:
    "0th = embed struct, 1st = oembed struct"
    embed = {}
    try:
        embed["title"] = str(data["title"])
        embed["description"] = str(data["description"]).replace(r"\n", "\n")
        embed["redirect"] = str(data["redirect"])
    except:
        return None
    
    try:
        if "#" in data["color"]:
            embed["color"] = str(data["color"])
        else:
            embed["color"] = "#" + hex(int(data["color"])).replace("0x", "")
    except:
        embed["color"] = None
    
    try:
        tmp = {}
        tmp["name"] = str(data["author"]["name"])
        tmp["url"] = str(data["author"]["url"])
        embed["author"] = tmp
    except:
        embed["author"] = None

    try:
        tmp = {}
        tmp["name"] = str(data["provider"]["name"])
        tmp["url"] = str(data["provider"]["url"])
        embed["provider"] = tmp
    except:
        embed["provider"] = None

    try:
        tmp = {}
        tmp["thumbnail"] = bool(data["image"]["thumbnail"])
        tmp["url"] = str(data["image"]["url"])
        embed["image"] = tmp
    except:
        embed["image"] = None
            
    return embed

def blacklist_check(ip):
    exc_time = time.time()
    db = DataBase(_config.db_name)
    blacklists = db.query("blacklist", ["ip", "reason", "timestamp", "expire"], {"ip": ip}, False)
    db.close()
    for bl in blacklists:
        if bl[4] == "0":
            return utils.returnJSON({"error": "ERROR_BLACKLIST", "message": "You are permanently blacklisted from this service.", "reason": bl[2], "expires": False})
        
        else:
            expires = float(bl[3]) + float(bl[4])
            if expires > exc_time:
                return utils.returnJSON({"error": "ERROR_BLACKLIST", "message": "You are blacklisted from this service.", "reason": bl[2], "expires": expires})
    return False

@app.route('/api/v1/embed', methods=["GET"])
@limiter.limit(f"{_config.get_rate_limit_per_min}/minute")
@limiter.limit(f"{_config.get_rate_limit_per_hour}/hour")
def fetch_embed():
    ip = utils.returnIP()
    blacklist = blacklist_check(ip)
    if blacklist != False: return blacklist, 403
    
    id_req = request.args.get("id")
    if id_req == None:
        return utils.returnJSON({"error": "ERROR_ID_NOT_PROVIDED", "message": "No Embed ID was found/provided."}), 400
    
    db = DataBase(_config.db_name)
    data = db.query("embeds", ["data", "id", "timestamp"], {"id": id_req})
    if data == None:
        return utils.returnJSON({"error": "ERROR_DATA_NOT_FOUND", "message": "Embed not found using provided ID."}), 404

    return utils.returnJSON(
        {
            "id": data[2],
            "link": f"{_config.url}{data[2]}",
            "timestamp": str(data[3]),
            "embed": json.loads(base64.b64decode(data[1].encode("utf-8")).decode("utf-8"))
        }
    ), 200


@app.route('/api/v1/embed', methods=["POST"])
@limiter.limit(f"{_config.post_rate_limit_per_min}/minute", deduct_when=lambda response: response.status_code == 201 or response.status_code == 200)
@limiter.limit(f"{_config.post_rate_limit_per_hour}/hour", deduct_when=lambda response: response.status_code == 201 or response.status_code == 200)
def create_embed():
    ip = utils.returnIP()
    req_time = time.time()
    blacklist = blacklist_check(ip)
    if blacklist != False: return blacklist, 403
    
    ctx = request.get_json()
    if ctx == None:
        return utils.returnJSON({"error": "ERROR_FETCHING_DATA", "message": "Invalid JSON, check headers and/or content."}), 400
    
    embed = parse_embed(ctx)
    if embed == None:
        return utils.returnJSON({"error": "ERROR_PARSING_DATA", "message": "Invalid JSON, check content."}), 400
    
    db = DataBase(_config.db_name)
    rand_id = None
    for _ in range(5):
        rand_id = utils.randChars(_config.id_length)
        if db.query("embeds", ["id"], {"id": rand_id}) == None:
            break
    if rand_id == None:
        db.close()
        return utils.returnJSON({"error": "ERROR_RANDOM_ID", "message": "Internal Error, send request again."}), 508
    
    b64embed = base64.b64encode(json.dumps(embed, separators=(",", ":")).encode("utf-8")).decode("utf-8")
    exist_check = db.query("embeds", ["data", "id", "timestamp"], {"data": b64embed})
    if exist_check != None:
        db.close()
        return utils.returnJSON(
        {
            "id": exist_check[2],
            "link": f"{_config.url}{exist_check[2]}",
            "timestamp": str(exist_check[3]),
            "embed": embed
        }
    ), 200


    db.insert("embeds", [ip, base64.b64encode(json.dumps(embed, separators=(",", ":")).encode("utf-8")).decode("utf-8"), rand_id, str(req_time)])
    db.close()

    return utils.returnJSON(
        {
            "id": rand_id,
            "link": f"{_config.url}{rand_id}",
            "timestamp": str(req_time),
            "embed": embed
        }
    ), 201


@app.route('/api/v1/ping')
@limiter.exempt
def ping():
    return utils.returnJSON({}), 200

@app.route('/e/<path:path>')
def open_embed(path):
    path = path.replace("/", "")
    db = DataBase(_config.db_name)
    data = db.query("embeds", ["data", "id", "timestamp"], {"id": path})
    if data == None:
        return render_template("404.html"), 404

    embed = json.loads(base64.b64decode(data[1].encode("utf-8")).decode("utf-8"))

    image = False
    try: image = embed["image"]
    except: pass
    if image == False or image == None:
        image = {"url": False, "thumbnail": False}
    
    color = False
    try: color = embed["color"]
    except: pass
    if color == False or color == None:
        color = False

    ua = request.headers.get('User-Agent').lower()
    
    for header in browsers:
        if header in ua:
            res = flask.make_response()
            res.headers['location'] = embed["redirect"]
            return res, 302
    
    return render_template("embed.html",
        new_url = embed["redirect"],
        title = embed["title"],
        description = embed["description"],
        o_url = _config.url2,
        image = image["url"],
        thumbnail = image["thumbnail"],
        color = color,
        id = path
    ), 200

@app.route('/o/<path:path>')
def oembed_json(path):
    path = path.replace(".json", "")
    
    db = DataBase(_config.db_name)
    data = db.query("embeds", ["data", "id", "timestamp"], {"id": path})
    if data == None:
        return render_template("404.html"), 404

    embed = json.loads(base64.b64decode(data[1].encode("utf-8")).decode("utf-8"))

    data = {}

    try: 
        data["author_name"] = embed["author"]["name"]
        data["author_url"] = embed["author"]["url"]
    except: pass
    try: 
        data["provider_name"] = embed["provider"]["name"]
        data["provider_url"] = embed["provider"]["url"]
    except: pass

    return utils.returnJSON(data), 200

@app.route('/assets/<path:path>')
@limiter.exempt
def send_js(path):
    return send_from_directory('assets', path)

@app.route('/vendors/<path:path>')
@limiter.exempt
def send_js2(path):
    return send_from_directory('vendors', path)

@app.route('/')
@limiter.exempt
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run('0.0.0.0',8080)