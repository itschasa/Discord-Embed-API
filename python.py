import requests

embed_data = {
    "title": "Want to advertise YOUR SHOP?",
    "description": "💜 - Mass DM on Discord to MILLIONS of users!\n💸 - Tokens starting from $0.02!\n🤩 - Get MORE SALES + MORE PROFIT on your shop!\n\nGet Started Today!",
    "redirect": "https://discord.gg/invite",
    "color": "#7289da",
    "provider": {
        "name": "Click here to view our sellix!",
        "url": "https://shop.sellix.io/"
    },
    "image": {
        "thumbnail": False,
        "url": "https://i.imgur.com/7v2sRvV.jpg"
    }
}

response = requests.post(f"https://e.chasa.wtf/api/v1/embed", json=embed_data)

if response.status_code == 200:
    print("Embed already existed")
    print(response.json()['link'])

elif response.status_code == 201:
    print("Created Embed")
    print(response.json()['link'])

elif response.status_code == 403:
    print("You've been blacklisted")
    print(response.json()['error'])
    print(response.json()['message'])
    print(response.json()['reason'])
    print("Doesn't Expire" if response.json()['expires'] == False else "Does Expire")

else:
    print(f"Error Code: {response.status_code}")
    print(response.json()['error'])
    print(response.json()['message'])
