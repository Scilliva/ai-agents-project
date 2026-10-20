"""Block 3: an A2A-style channel, demonstrated. Given complete, no TODOs.

    python 03_a2a.py

Eight minutes, one command, two processes, four questions. There is nothing
to complete here and that is a scheduling decision rather than a claim about
A2A: ninety minutes does not hold three build blocks, and a block everybody
starts and nobody finishes teaches less than a demonstration everybody
watches. Building the channel yourself is the take-home.

Standard library only. No key, no model, no network beyond localhost.

This is A2A-STYLE, not a certified implementation. Three pieces carry the
concepts and the vocabulary transfers: the agent card, the task lifecycle,
and the artifact.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8971

# The card. A remote agent publishes what it can do, so a client decides from
# declared skills rather than from a configuration file somebody has to keep
# up to date. That is capability discovery, and it is why the card is fetched
# rather than hard coded.
CARD = {
    "name": "translation-agent",
    "description": "Translates short administrative texts.",
    "url": f"http://127.0.0.1:{PORT}",
    "version": "1.0",
    "skills": [{
        "id": "translate",
        "name": "Translate a short text",
        "description": "Translates between French, German, and English.",
        "inputModes": ["text/plain"],
        "outputModes": ["text/plain"],
    }],
}

GLOSSARY = {
    "Bierger-Center": "Bierger-Center",
    "opening hours": "heures d'ouverture",
    "waste collection": "collecte des dechets",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):        # keep the demonstration readable
        pass

    def do_GET(self):
        if self.path == "/.well-known/agent.json":
            self._send(200, CARD)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        request = json.loads(self.rfile.read(length) or b"{}")
        text = request.get("message", {}).get("parts", [{}])[0].get("text", "")
        task_id = request.get("taskId", "task-1")

        # The task lifecycle. A remote agent does not simply return a value:
        # it accepts a task, works, and ends in a terminal state. The client
        # has to handle every one of those states, including the ones it
        # would rather not think about.
        if "FAIL" in text:
            self._send(200, {"taskId": task_id, "state": "failed",
                             "error": "the glossary does not cover this text"})
            return
        if "SLOW" in text:
            time.sleep(5)             # longer than the client's timeout
            self._send(200, {"taskId": task_id, "state": "completed",
                             "artifact": {"parts": [{"text": "too late"}]}})
            return
        if "EMPTY" in text:
            self._send(200, {"taskId": task_id, "state": "completed",
                             "artifact": {"parts": [{"data": {"x": 1}}]}})
            return

        translated = GLOSSARY.get(text.strip(), f"[fr] {text.strip()}")
        self._send(200, {"taskId": task_id, "state": "completed",
                         "artifact": {"parts": [{"text": translated}]}})

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve():
    # Threading, not the plain HTTPServer. The slow task sleeps for five
    # seconds, and a single threaded server would block every later request
    # behind it, so the timeout demonstration would poison the one after it.
    # A remote agent that serializes all callers behind its slowest one is a
    # real failure mode, and it is worth not accidentally demonstrating it
    # here while trying to demonstrate something else.
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


def fetch_card() -> dict:
    with urllib.request.urlopen(
            f"http://127.0.0.1:{PORT}/.well-known/agent.json", timeout=5) as r:
        return json.loads(r.read())


def delegate(text: str, task_id: str, timeout: float = 3.0) -> dict:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/",
        data=json.dumps({"taskId": task_id,
                         "message": {"parts": [{"text": text}]}}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as r:
        return json.loads(r.read())


def main() -> int:
    server = mp.Process(target=serve, daemon=True)
    server.start()
    time.sleep(1.5)

    try:
        card = fetch_card()
        skills = [s["id"] for s in card["skills"]]
        print(f"card fetched: {card['name']}, skills {skills}\n")

        # Question 1: delegated, because the card declares the skill.
        print("1 delegated")
        print(f"   -> {delegate('opening hours', 'task-1')}")

        # Question 2: NOT delegated. The client checks the card first and
        # this is not a skill the remote agent claims. Deciding locally costs
        # nothing; discovering it after a round trip costs a round trip.
        print("\n2 not delegated")
        if "summarize" not in skills:
            print("   -> the card declares no 'summarize' skill, so this is "
                  "handled locally and no request is sent")

        # Question 3: the remote agent failed. A failure is a state, not an
        # exception, and the client has to decide what to do with it.
        print("\n3 failed")
        result = delegate("FAIL please", "task-3")
        print(f"   -> {result}")
        print("   policy here: fall back to the local glossary and mark the "
              "answer degraded. Escalating to a human is equally defensible.")

        # Question 4: the remote agent timed out. Note that the task id is
        # kept. The work may still be running on the other side, and throwing
        # the id away means you can never ask again or cancel it.
        print("\n4 timed out")
        try:
            delegate("SLOW please", "task-4", timeout=2.0)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"   -> timeout after 2.0s ({type(exc).__name__})")
            print("   the task id 'task-4' is kept, because the work may "
                  "still be running and an abandoned id cannot be chased")

        # And the branch groups forget: an artifact with no text part.
        print("\n5 an artifact whose parts are not text")
        result = delegate("EMPTY please", "task-5")
        parts = result["artifact"]["parts"]
        if not any("text" in p for p in parts):
            print(f"   -> artifact has no text part: {parts}")
            print("   report the mismatch rather than stringifying it. An "
                  "agent that coerces unknown output into a string is an "
                  "agent that will one day show a resident a dict.")
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    mp.set_start_method("spawn")
    raise SystemExit(main())
