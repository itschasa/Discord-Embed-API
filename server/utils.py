import random, json
from flask import request, render_template

def randChars(length):
    x = ""
    for _ in range(length):
        x += random.choice("QWERTYUIOPLKJHGFDSAZXCVBNM1234567890qwertyuioplkjhgfdsazxcvbnm")
    return x

def returnIP():
    return request.access_route[0]

def returnJSON(js):
    return json.dumps(js)