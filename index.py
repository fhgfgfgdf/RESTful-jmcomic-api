import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cloud-functions"))
from backend import app

_inner = app.wsgi_app


def _strip_entry(environ, start_response):
    """vercel.json rewrites every path to /index.py, and Vercel hands the
    rewritten path to the function, so Flask would see /index.py instead of
    /config. Move that prefix into SCRIPT_NAME before routing."""
    path = environ.get("PATH_INFO") or "/"
    if path == "/index.py" or path.startswith("/index.py/"):
        environ["SCRIPT_NAME"] = (environ.get("SCRIPT_NAME") or "") + "/index.py"
        environ["PATH_INFO"] = path[len("/index.py"):] or "/"
    return _inner(environ, start_response)


app.wsgi_app = _strip_entry

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","3002")))
