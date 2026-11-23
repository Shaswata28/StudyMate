import os
import socket
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread

import uvicorn

from app.main import create_app


def open_when_ready(server: uvicorn.Server, url: str):
    while not server.started and not server.should_exit:
        time.sleep(0.1)
    if server.started:
        webbrowser.open(url)


def main():
    if getattr(sys, "frozen", False):
        web_root = Path(sys._MEIPASS) / "web"
    else:
        web_root = Path(__file__).resolve().parents[1] / "frontend" / "out"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        server = uvicorn.Server(uvicorn.Config(create_app(web_root), host="127.0.0.1", port=port))
        print(f"StudyMate is opening at {url}. Keep this window open while studying.", flush=True)
        if not os.getenv("STUDYMATE_NO_BROWSER"):
            Thread(target=open_when_ready, args=(server, url), daemon=True).start()
        server.run(sockets=[listener])


if __name__ == "__main__":
    main()
