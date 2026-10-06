import sys
from agent import run_task
from tasks import BY_ID
from project.models import BASE_URL, API_KEY, LARGE

if "--replay" in sys.argv:
    from project.fixtures import ReplayClient
    client = ReplayClient.from_lab("week04_react_tool_use")
else:
    from openai import OpenAI
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

for tid in sys.argv[1:] or ["T-01"]:
    if tid.startswith("--"):
        continue
    run = run_task(client, BY_ID[tid], model=LARGE.name)
    print(tid, "steps", run.steps, "tools", run.tool_calls,
          "cap", run.cap_fired, "errors", run.tool_errors,
          "injection_seen", run.saw_injection)
    print("   ", run.answer)