"""Pruebas reales de Deployment y ReplicaSet, solo en el cluster sarseg-p2."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import threading
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NS = "sarseg-observabilidad"
BASE = "http://127.0.0.1:13000"
KUBECTL = ["kubectl", "--context", "kind-sarseg-p2"]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/evidencias/ejecucion")
    parser.add_argument("--render", action="store_true", help="Exportar capturas con el renderer local")
    parser.add_argument("--context", default="kind-sarseg-p2", choices=["kind-sarseg-p2", "kind-sarseg-p2-evidencia"])
    parser.add_argument("--base-url", default="http://127.0.0.1:13000", choices=["http://127.0.0.1:13000", "http://127.0.0.1:13010"])
    args = parser.parse_args()
    global BASE, KUBECTL
    BASE = args.base_url
    KUBECTL = ["kubectl", "--context", args.context]
    expected_url = "http://127.0.0.1:13010" if args.context.endswith("-evidencia") else "http://127.0.0.1:13000"
    if BASE != expected_url:
        raise SystemExit("El contexto y el puerto deben corresponder al mismo laboratorio.")
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    if (out / "resultados.json").exists():
        raise SystemExit("La evidencia ya existe. Usa --output con otra carpeta para conservarla.")
    records = []
    samples = []
    stop = threading.Event()
    result = {"started_utc": now(), "context": args.context, "base_url": BASE, "namespace": NS, "checks": {}}

    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def command(*parts, namespaced=True, expected=0):
        cmd = KUBECTL + (["-n", NS] if namespaced else []) + list(parts)
        completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=330)
        records.append({"time_utc": now(), "command": subprocess.list2cmdline(cmd), "exit_code": completed.returncode,
                        "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != expected:
            raise RuntimeError(f"{cmd}: {completed.stderr}")
        return completed.stdout

    def get(kind, *extra):
        return json.loads(command("get", kind, *extra, "-o", "json"))

    def http(path):
        with urllib.request.urlopen(BASE + path, timeout=10) as response:
            return response.status, json.load(response)

    def mark(name, detail):
        result["checks"][name] = {"passed": True, "detail": detail, "time_utc": now()}
        print("PASS", name, flush=True)

    def snapshot(name):
        data = get("deployments,replicasets,pods,services,endpointslices")
        save(name + ".json", data)
        (out / (name + ".txt")).write_text(command("get", "deploy,rs,pod,svc", "-o", "wide"), encoding="utf-8")
        return data

    def live_pods():
        return [p for p in get("pods", "-l", "app=grafana")["items"] if not p["metadata"].get("deletionTimestamp")]

    def ready(p):
        return any(c["type"] == "Ready" and c["status"] == "True" for c in p["status"].get("conditions", []))

    def active_rs():
        candidates = [r for r in get("replicasets", "-l", "app=grafana")["items"] if r["spec"].get("replicas", 0) > 0]
        assert len(candidates) == 1, "Se esperaba un ReplicaSet activo despues del rollout"
        return candidates[0]

    def wait_replicas(number, absent_uid=None):
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            pods = live_pods()
            dep = get("deployment/grafana")
            if (len(pods) == number and all(ready(p) for p in pods)
                    and dep["status"].get("availableReplicas") == number
                    and all(p["metadata"]["uid"] != absent_uid for p in pods)):
                return pods
            time.sleep(2)
        raise TimeoutError(f"No se alcanzaron {number} replicas listas")

    def render(name):
        if not args.render:
            return
        token = (ROOT / ".local/renderer-token.txt").read_text().strip()
        node_name = "sarseg-p2-evidencia-control-plane" if args.context.endswith("-evidencia") else "sarseg-p2-control-plane"
        target = "http://" + node_name + ":30300/d/sarseg-operacion/sarseg?orgId=1&from=now-15m&to=now&kiosk=tv"
        query = urllib.parse.urlencode({"url": target, "width": 1500, "height": 950,
                                       "deviceScaleFactor": 1, "timeout": 90, "encoding": "png"})
        req = urllib.request.Request("http://127.0.0.1:18081/render?" + query, headers={"X-Auth-Token": token})
        with urllib.request.urlopen(req, timeout=120) as response:
            data = response.read()
        assert data.startswith(b"\x89PNG\r\n\x1a\n"), "El renderer no devolvio PNG"
        captures = out / "capturas"
        captures.mkdir(exist_ok=True)
        (captures / name).write_bytes(data)

    def sample_health():
        while not stop.is_set():
            start = time.monotonic()
            try:
                status, health = http("/api/health")
                samples.append({"time_utc": now(), "http": status, "database": health.get("database"),
                                "duration_ms": round((time.monotonic() - start) * 1000, 2)})
            except Exception as exc:
                samples.append({"time_utc": now(), "http": 0, "error": type(exc).__name__})
            stop.wait(1)

    worker = threading.Thread(target=sample_health, daemon=True)
    try:
        command("rollout", "status", "deployment/grafana", "--timeout=300s")
        nodes = json.loads(command("get", "nodes", "-o", "json", namespaced=False))
        save("nodos.json", nodes)
        assert len(nodes["items"]) == 3
        assert all(any(c["type"] == "Ready" and c["status"] == "True" for c in n["status"]["conditions"]) for n in nodes["items"])
        mark("cluster", "3 nodos Ready con Kubernetes " + nodes["items"][0]["status"]["nodeInfo"]["kubeletVersion"])
        original = get("deployment/grafana")
        assert original["spec"]["replicas"] == 2, "La prueba debe comenzar con dos replicas"
        initial_revision = original["metadata"]["annotations"]["deployment.kubernetes.io/revision"]
        initial_rs = active_rs()
        pods = wait_replicas(2)
        assert initial_rs["metadata"]["ownerReferences"][0]["uid"] == original["metadata"]["uid"]
        assert all(p["metadata"]["ownerReferences"][0]["uid"] == initial_rs["metadata"]["uid"] for p in pods)
        assert len({p["spec"]["nodeName"] for p in pods}) == 2
        result["ownership"] = {"deployment": original["metadata"]["name"], "deployment_uid": original["metadata"]["uid"],
                               "replicaset": initial_rs["metadata"]["name"], "replicaset_uid": initial_rs["metadata"]["uid"],
                               "pods": [{"name": p["metadata"]["name"], "uid": p["metadata"]["uid"], "node": p["spec"]["nodeName"]} for p in pods]}
        mark("ownership", "ownerReferences unen Deployment, ReplicaSet y dos Pods en workers distintos")
        status, health = http("/api/health")
        assert status == 200 and health["database"] == "ok"
        save("grafana-health.json", {"url": BASE + "/api/health", "http": status, "response": health, "time_utc": now()})
        svc = get("service/grafana")
        assert svc["spec"]["type"] == "NodePort" and svc["spec"]["ports"][0]["nodePort"] == 30300
        mark("exposure", "HTTP 200 en " + BASE + " y Service NodePort 30300")
        dashboard = http("/api/dashboards/uid/sarseg-operacion")[1]
        assert len(dashboard["dashboard"]["panels"]) == 7
        save("dashboard-api.json", dashboard)
        query = urllib.parse.quote("up")
        metrics = http("/api/datasources/proxy/uid/prometheus-sarseg/api/v1/query?query=" + query)[1]
        assert len(metrics["data"]["result"]) == 3
        assert all(m["value"][1] == "1" for m in metrics["data"]["result"])
        save("prometheus-up.json", metrics)
        mark("metrics", "Dashboard provisionado y tres fuentes de Prometheus con up=1")
        account = "--as=system:serviceaccount:" + NS + ":kube-state-metrics"
        assert command("auth", "can-i", "list", "pods", account).strip() == "yes"
        assert command("auth", "can-i", "list", "secrets", account, expected=1).strip() == "no"
        mark("rbac", "kube-state-metrics puede listar Pods y no puede listar Secrets")
        snapshot("01-inicial")
        render("01-grafana-inicial.png")
        worker.start()
        command("scale", "deployment/grafana", "--replicas=3")
        wait_replicas(3)
        scaled_rs = active_rs()
        assert scaled_rs["metadata"]["uid"] == initial_rs["metadata"]["uid"]
        snapshot("02-escalado-tres")
        time.sleep(7)
        render("02-grafana-tres-replicas.png")
        mark("scale_up", "2 -> 3 Pods Ready; se mantiene el mismo ReplicaSet")
        command("scale", "deployment/grafana", "--replicas=2")
        wait_replicas(2)
        mark("scale_down", "3 -> 2 replicas disponibles")
        victim = live_pods()[0]
        start = time.monotonic()
        command("delete", "pod", victim["metadata"]["name"], "--wait=false")
        healed = wait_replicas(2, absent_uid=victim["metadata"]["uid"])
        replacement = [p for p in healed if p["metadata"]["uid"] not in {v["uid"] for v in result["ownership"]["pods"]}]
        assert replacement
        result["recovery"] = {"deleted_pod": victim["metadata"]["name"], "deleted_uid": victim["metadata"]["uid"],
                              "new_pods": [{"name": p["metadata"]["name"], "uid": p["metadata"]["uid"]} for p in replacement],
                              "elapsed_seconds": round(time.monotonic() - start, 2)}
        snapshot("03-recuperacion")
        mark("self_healing", "ReplicaSet repone el Pod eliminado con un UID nuevo")
        patch = {"metadata": {"annotations": {"kubernetes.io/change-cause": "Prueba P2 de actualizacion de plantilla"}},
                 "spec": {"template": {"metadata": {"annotations": {"sarseg.io/revision-laboratorio": "v2-prueba-p2"}}}}}
        command("patch", "deployment", "grafana", "--type=merge", "-p", json.dumps(patch))
        snapshot("04-inicio-rollout")
        command("rollout", "status", "deployment/grafana", "--timeout=300s")
        wait_replicas(2)
        updated_rs = active_rs()
        assert updated_rs["metadata"]["uid"] != initial_rs["metadata"]["uid"]
        snapshot("05-rollout-completo")
        result["rollout"] = {"before_rs": initial_rs["metadata"]["name"], "after_rs": updated_rs["metadata"]["name"],
                             "initial_revision": initial_revision,
                             "updated_revision": get("deployment/grafana")["metadata"]["annotations"]["deployment.kubernetes.io/revision"],
                             "change": "Solo anotacion de spec.template; misma imagen grafana/grafana:12.3.0"}
        mark("rolling_update", "Cambio de spec.template crea un ReplicaSet diferente con maxUnavailable=0")
        command("rollout", "undo", "deployment/grafana", "--to-revision=" + initial_revision)
        command("rollout", "status", "deployment/grafana", "--timeout=300s")
        wait_replicas(2)
        restored_rs = active_rs()
        assert restored_rs["metadata"]["uid"] == initial_rs["metadata"]["uid"]
        assert get("deployment/grafana")["spec"]["template"]["metadata"]["annotations"]["sarseg.io/revision-laboratorio"] == "v1"
        snapshot("06-rollback")
        result["rollout"]["rollback_rs"] = restored_rs["metadata"]["name"]
        mark("rollback", "Se recupera la plantilla v1 y se reactiva su ReplicaSet")
        time.sleep(7)
        render("03-grafana-final.png")
        (out / "deployment-describe.txt").write_text(command("describe", "deployment", "grafana"), encoding="utf-8")
        (out / "eventos.txt").write_text(command("get", "events", "--sort-by=.metadata.creationTimestamp"), encoding="utf-8")
        (out / "historial-rollout.txt").write_text(command("rollout", "history", "deployment/grafana"), encoding="utf-8")
        save("versiones.json", json.loads(command("version", "-o", "json", namespaced=False)))
        result["success"] = True
    except Exception as exc:
        result["success"] = False
        result["error"] = str(exc)
        raise
    finally:
        stop.set()
        if worker.is_alive():
            worker.join(timeout=12)
        save("http-muestreo.json", samples)
        if samples:
            good = sum(s.get("http") == 200 and s.get("database") == "ok" for s in samples)
            result["http_sampling"] = {"total": len(samples), "successful": good, "failed": len(samples) - good,
                                       "interval_seconds": 1, "scope": "Escalado, eliminacion de Pod, rollout y rollback"}
            if good == len(samples):
                mark("http_sampling", f"{good}/{len(samples)} muestras HTTP 200; muestreo, no prueba de disponibilidad absoluta")
            else:
                result["success"] = False
        result["finished_utc"] = now()
        save("resultados.json", result)
        save("comandos.json", records)
        transcript = "\n\n".join(f"[{r['time_utc']}] $ {r['command']}\nexit={r['exit_code']}\n{r['stdout']}{r['stderr']}" for r in records)
        (out / "comandos.txt").write_text(transcript, encoding="utf-8")
    if not result["success"]:
        raise SystemExit("Prueba incompleta o muestras HTTP fallidas: revisa resultados.json")
    print(json.dumps(result["http_sampling"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
