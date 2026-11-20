"""Local Git polling adapter. ONLY Spinnaker deploys the Git manifests.

No kubectl or Kubernetes credentials are used by this adapter. Successful
revision state advances only when Orca reports a SUCCEEDED execution.
"""
import argparse
import hashlib
import json
import logging
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT.parent / ".local/spinnaker"
REPOSITORY = "https://github.com/JOURT1/SARSEG-Kubernetes-P2.git"
RAW = "https://raw.githubusercontent.com/JOURT1/SARSEG-Kubernetes-P2"
GATE = "http://127.0.0.1:14884"
FILES = ["deployment.yml", "service.yml", "hpa.yml"]


def request(path, data=None):
    url = path if path.startswith("https://") else GATE + path
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "SARSEG-local-lab"})
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read()
        try:
            return json.loads(body)
        except ValueError:
            return body.decode()


def resolve_revision(branch):
    result = subprocess.run(["git", "ls-remote", REPOSITORY, "refs/heads/" + branch],
        capture_output=True, text=True, check=True, timeout=30)
    sha = result.stdout.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid Git revision")
    artifacts, contents = [], []
    for name in FILES:
        url = f"{RAW}/{sha}/spinnaker/k8s/{name}"
        with urllib.request.urlopen(url, timeout=30) as response:
            contents.append(response.read())
        artifacts.append({"type": "http/file", "name": name, "reference": url,
                          "version": sha, "artifactAccount": "public-git-http"})
    digest = hashlib.sha256(b"\0".join(contents)).hexdigest()
    return sha, digest, artifacts


def tick(branch):
    state_path = LOCAL / "watch-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    sha, digest, artifacts = resolve_revision(branch)
    if state.get("digest") == digest:
        return False
    logging.info("Git changed: %s; starting Spinnaker", sha)
    response = request("/pipelines/sarseg/deploy-git", {"type": "manual", "user": "local-git-poller",
        "parameters": {"gitSha": sha, "gitBranch": branch}, "artifacts": artifacts})
    ref = response["ref"]
    if not ref.startswith("/pipelines/"):
        raise ValueError(f"Unexpected execution reference: {ref}")
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        result = request(ref)
        status = result.get("status")
        if status == "SUCCEEDED":
            state = {"sha": sha, "digest": digest, "execution": ref, "branch": branch,
                     "completedAt": datetime.now(timezone.utc).isoformat()}
            state_path.write_text(json.dumps(state, indent=2))
            (LOCAL / "last-execution.json").write_text(json.dumps(result, indent=2))
            with (LOCAL / "watch-events.jsonl").open("a") as stream:
                stream.write(json.dumps(state) + "\n")
            logging.info("Spinnaker SUCCEEDED: %s", ref)
            return True
        if status in ["TERMINAL", "CANCELED", "STOPPED"]:
            (LOCAL / "failed-execution.json").write_text(json.dumps(result, indent=2))
            raise RuntimeError(f"Spinnaker {status}: {ref}; revision NOT acknowledged")
        time.sleep(5)
    raise TimeoutError("Spinnaker execution exceeded 10 minutes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default="codex/spinnaker-local")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    LOCAL.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    while True:
        try:
            tick(args.branch)
        except Exception:
            logging.exception("Git polling failed; will retry without advancing revision")
            if args.once:
                raise
        if args.once:
            break
        time.sleep(20)


if __name__ == "__main__":
    main()
