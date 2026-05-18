"""Production server entrypoint for hosting platforms (Render, Railway, etc).

When hosting this on a real server, use:
    gunicorn wsgi:app
    
Locally, just run server.py directly.
"""
from server import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
