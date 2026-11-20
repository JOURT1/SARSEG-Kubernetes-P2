"""Exercise Git -> Spinnaker -> Kubernetes and real CPU-driven HPA scaling.

--publish-change creates and pushes ONE manifest commit on the current lab
branch. No manual apply/scale is used for the three assignment resources.
"""
import argparse
from datetime import datetime, timezone
from html import escape
import http.cookiejar
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import yaml
from git_watch import request, LOCAL

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "docs/evidencias"
K = ["kubectl", "--context", "kind-sarseg-spinnaker"]
RESULTS = []
SKIP_SCREENSHOTS = False


def run(args):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    return r.stdout


def resource(kind, name):
    return json.loads(run(K + ["-n", "sarseg-dev", "get", kind, name, "-o", "json"]))


def check(name, condition, detail):
    RESULTS.append({"check": name, "passed": bool(condition), "detail": detail})
    (OUT / "results.json").write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")
    print(name, "PASS" if condition else "FAIL", detail, flush=True)
    assert condition, name


def snapshot(key, title, note):
    commands = [K + ["-n", "sarseg-dev", "get", "deployment,service,hpa,pods"],
                K + ["-n", "sarseg-dev", "top", "pods"],
                K + ["-n", "sarseg-dev", "get", "hpa", "sarseg-web", "-o", "yaml"]]
    blocks = [{"command": subprocess.list2cmdline(c), "output": run(c)} for c in commands]
    state = {"time": datetime.now(timezone.utc).isoformat(), "title": title, "note": note, "blocks": blocks}
    (OUT / (key + ".json")).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    body = ''.join('<h2>' + escape(b['command']) + '</h2><pre>' + escape(b['output']) + '</pre>' for b in blocks[:2])
    hpa = resource("hpa", "sarseg-web")
    text = json.dumps({"spec": hpa["spec"], "status": hpa.get("status")}, indent=2)
    html = '<!doctype html><html lang="es"><meta charset="utf-8"><title>' + escape(title) + '</title><style>body{margin:0;padding:36px;background:#f4f7fa;color:#12273b;font:17px Arial}header{color:#246782;font-size:16px;font-weight:bold;letter-spacing:2px}h1{font-size:32px;margin:12px 0}p{line-height:1.5}h2{font:15px Consolas;margin-top:24px}pre{background:white;padding:18px;border:1px solid #ccd6df;font:15px/1.5 Consolas;white-space:pre-wrap}footer{margin-top:20px;font-size:13px;color:#526477}</style><header>SARSEG / SPINNAKER / EVIDENCIA REAL</header><h1>' + escape(title) + '</h1><p>' + escape(note) + '</p><p>' + state['time'] + ' · contexto kind-sarseg-spinnaker</p>' + body + '<details><summary>HPA original</summary><pre>' + escape(text) + '</pre></details><footer>Visor de salidas originales de kubectl. Captura de un registro de ejecución; no es una terminal ni un estado en vivo.</footer></html>'
    page = OUT / (key + ".html")
    page.write_text(html, encoding="utf-8")
    screenshot(page.as_uri(), key + ".png", full=True)


def screenshot(url, name, full=False):
    if SKIP_SCREENSHOTS:
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / name), full_page=full)
        browser.close()


def monitor_until(predicate, timeout, filename):
    end = time.monotonic() + timeout
    samples = []
    while time.monotonic() < end:
        dep, hpa = resource("deployment", "sarseg-web"), resource("hpa", "sarseg-web")
        samples.append({"time": datetime.now(timezone.utc).isoformat(), "deployment": dep.get("status"), "hpa": hpa.get("status")})
        (OUT / filename).write_text(json.dumps(samples, indent=2), encoding="utf-8")
        print("HPA", samples[-1]["time"], "ready=", dep.get("status",{}).get("readyReplicas"),
              "current=", hpa.get("status",{}).get("currentReplicas"), "desired=", hpa.get("status",{}).get("desiredReplicas"), flush=True)
        if predicate(dep, hpa):
            return dep, hpa
        time.sleep(10)
    raise TimeoutError("Expected autoscaling state not reached")


def main():
    global SKIP_SCREENSHOTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-change", action="store_true")
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()
    SKIP_SCREENSHOTS = args.no_screenshots
    OUT.mkdir(parents=True, exist_ok=True)
    dep, svc, hpa = [resource(*x) for x in [("deployment", "sarseg-web"), ("service", "sarseg-web"), ("hpa", "sarseg-web")]]
    check("initial-two-ready", dep["spec"]["replicas"] == dep["status"].get("readyReplicas") == 2, "2 Pods Ready")
    check("resources-and-selectors", dep["spec"]["selector"]["matchLabels"] == svc["spec"]["selector"] and bool(dep["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]), "Service and Deployment labels match; CPU request configured")
    check("nodeport", svc["spec"]["type"] == "NodePort" and svc["spec"]["ports"][0]["nodePort"] == 30380, "80 -> named http -> 8080; NodePort 30380 -> localhost:14800")
    check("hpa-spec", hpa["spec"]["minReplicas"] == 2 and hpa["spec"]["maxReplicas"] == 5 and hpa["spec"]["metrics"][0]["resource"]["target"]["averageUtilization"] == 50, "min=2 max=5 CPU=50%")
    ready = json.loads(urllib.request.urlopen("http://127.0.0.1:14800/health/ready").read())
    check("web-and-api", urllib.request.urlopen("http://127.0.0.1:14800").status == 200 and ready["status"] == "ready", "HTTP 200 web and API database readiness")
    credentials = json.loads((LOCAL / "credentials.json").read_text())
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    login = urllib.request.Request("http://127.0.0.1:14800/api/v1/auth/login", data=json.dumps({"username": "admin", "password": credentials["ADMIN_PASSWORD"]}).encode(), headers={"Content-Type": "application/json"})
    with opener.open(login) as response:
        check("real-sarseg-login", response.status == 200, "Admin login HTTP 200; credentials and response excluded from evidence")
    metrics = json.loads(run(K + ["get", "--raw", "/apis/metrics.k8s.io/v1beta1/namespaces/sarseg-dev/pods"]))
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    check("metrics-server", any(x["metadata"]["name"].startswith("sarseg-web-") for x in metrics["items"]), "CPU and memory metrics available for SARSEG Pods")
    snapshot("01-inicial", "Dos réplicas y servicio accesible", "Deployment, Service NodePort y HPA instalados por Spinnaker desde Git.")
    screenshot("http://127.0.0.1:14800", "02-sarseg-web.png")
    state = json.loads((LOCAL / "watch-state.json").read_text())
    (OUT / "initial-execution.json").write_text((LOCAL / "last-execution.json").read_text())
    if args.publish_change:
        before_id = state["execution"]
        manifest = ROOT / "k8s/deployment.yml"
        revision = "gitops-verificado-" + datetime.now(timezone.utc).strftime("%H%M%S")
        text = manifest.read_text()
        import re
        text = re.sub(r"sarseg.edu/revision: '[^']+'", "sarseg.edu/revision: '" + revision + "'", text)
        manifest.write_text(text)
        run(["git", "add", "spinnaker/k8s/deployment.yml"])
        run(["git", "commit", "-m", "test(gitops): publish SARSEG revision for automatic deployment proof"])
        run(["git", "push"])
        sha = run(["git", "rev-parse", "HEAD"]).strip()
        end = time.monotonic() + 480
        while time.monotonic() < end:
            state = json.loads((LOCAL / "watch-state.json").read_text())
            if state.get("sha") == sha:
                break
            time.sleep(5)
        dep = resource("deployment", "sarseg-web")
        check("automatic-git-deployment", state.get("sha") == sha and state["execution"] != before_id and dep["spec"]["template"]["metadata"]["annotations"]["sarseg.edu/revision"] == revision, f"commit {sha}; execution {state['execution']}; revision {revision}")
    execution = request(state["execution"])
    (OUT / "git-state.json").write_text(json.dumps(state, indent=2))
    (OUT / "git-execution.json").write_text(json.dumps(execution, indent=2))
    check("spinnaker-three-stages", execution["status"] == "SUCCEEDED" and sum(s["type"] == "deployManifest" and s["status"] == "SUCCEEDED" for s in execution["stages"]) == 3, "Deployment, Service and HPA artifact stages SUCCEEDED")
    screenshot("http://127.0.0.1:14900/#/applications/sarseg/executions", "03-spinnaker-pipeline.png")
    snapshot("04-git-sincronizado", "Cambio Git desplegado automáticamente", "El sondeo inicia Spinnaker; Clouddriver aplica los artefactos del SHA inmutable.")
    code = '''import concurrent.futures,time,urllib.request
end=time.monotonic()+240
def load(i):
 n=0
 while time.monotonic()<end:
  try:
   with urllib.request.urlopen('http://sarseg-web/?load='+str(n),timeout=3) as r:r.read()
   n+=1
  except Exception:pass
 return n
with concurrent.futures.ThreadPoolExecutor(max_workers=48) as p:print(sum(p.map(load,range(48))))
'''
    job = {"apiVersion": "batch/v1", "kind": "Job", "metadata": {"name": "sarseg-cpu-load", "namespace": "sarseg-dev"},
        "spec": {"backoffLimit": 0, "ttlSecondsAfterFinished": 300, "activeDeadlineSeconds": 260,
        "template": {"spec": {"restartPolicy": "Never", "containers": [{"name": "http-load", "image": "python:3.13-alpine", "command": ["python", "-u", "-c", code], "resources": {"requests": {"cpu": "250m", "memory": "64Mi"}, "limits": {"cpu": "1", "memory": "128Mi"}}}]}}}}
    (OUT / "load-job.yml").write_text(yaml.safe_dump(job, sort_keys=False))
    run(K + ["-n", "sarseg-dev", "delete", "job", "sarseg-cpu-load", "--ignore-not-found"])
    run(K + ["apply", "-f", str(OUT / "load-job.yml")])
    dep, hpa = monitor_until(lambda d,h: d["status"].get("readyReplicas",0) == 5 and h["status"].get("currentReplicas") == 5, 240, "hpa-up.json")
    check("cpu-scale-up", dep["status"].get("readyReplicas") == 5, "HPA increased from 2 to 5 Ready replicas under real HTTP load")
    snapshot("05-carga-cinco", "HPA: cinco réplicas bajo carga", "El HPA elevó las réplicas automáticamente. No se ejecutó kubectl scale.")
    run(K + ["-n", "sarseg-dev", "delete", "job", "sarseg-cpu-load", "--wait=true", "--timeout=30s"])
    dep, hpa = monitor_until(lambda d,h: d["spec"]["replicas"] == 2 and d["status"].get("replicas") == d["status"].get("readyReplicas") == 2 and h["status"].get("currentReplicas") == 2, 360, "hpa-down.json")
    check("cpu-scale-down", dep["status"].get("readyReplicas") == 2, "HPA returned from 5 to 2 Ready replicas after load stopped")
    snapshot("06-reduccion-dos", "HPA: regreso a dos réplicas", "Carga retirada; estabilización de reducción de 60 segundos.")
    (OUT / "events.txt").write_text(run(K + ["-n", "sarseg-dev", "get", "events", "--sort-by=.lastTimestamp"]), encoding="utf-8")
    (OUT / "platform.txt").write_text(run(K + ["-n", "spinnaker", "get", "pods,deployments,services"]), encoding="utf-8")
    (OUT / "versions.txt").write_text(run(K + ["version"]) + run(["docker", "version", "--format", "{{.Server.Version}}"]), encoding="utf-8")
    print("All checks passed", flush=True)


if __name__ == "__main__":
    main()
