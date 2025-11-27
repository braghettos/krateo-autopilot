import yaml
from pathlib import Path
from config import AGENTS, PORT

for agent in AGENTS:
    if agent == "root_agent":
        continue
    chart_values_file = Path(f"remote_agents/{agent}/chart/values.yaml")

    with open(chart_values_file, "r") as f:
        existing = yaml.safe_load(f) or {}

    if "service" not in existing:
        existing["service"] = {}

    existing["service"]["port"] = PORT[agent]

    with open(chart_values_file, "w") as f:
        yaml.dump(existing, f, sort_keys=False)

    print(f"Updated {chart_values_file} (service.port = {PORT[agent]})")
