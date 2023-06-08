## Discord Embed API
API that allows users to create urls that have a custom embed displayed on social media's (like Discord).

Feel free to host, use, steal, change, or take inspiration from this code.
Technical details about how to display embeds with html is in `technicals.html`.

### Example
The payload you'd send to the API for this embed is in the client folder.

![Example 1](https://raw.githubusercontent.com/itschasa/e.chasa.wtf/main/example_1.jpg)

### Deployment
This server is not the most efficient or cleanest setup, but it will work out of the box.

You will need to host the API on a server, with a domain pointing to it.

The default port is 8080, but this can be changed at the bottom of `web.py`.

In `_config.py`, change `url` and `url2` with the appropriate domain you are hosting on.
You can also change the rate limits if you want to.

By default, the server will run as a development server. You can use waitress, or another deployment server to host efficiently.