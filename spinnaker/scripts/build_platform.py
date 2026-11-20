"""Generate the small, local Spinnaker platform. No credentials in this file.

Based on the official spinnaker-kustomize installer at release 2026.4.1.
The selected SQL settings and Deck settings are vendored with their license.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = []


def add(kind, name, spec=None, api="v1", namespace="spinnaker", **kw):
    obj = {"apiVersion": api, "kind": kind, "metadata": {"name": name}}
    if namespace:
        obj["metadata"]["namespace"] = namespace
    if spec is not None:
        obj["spec"] = spec
    obj.update(kw)
    OUT.append(obj)
    return obj


def service(name, port, node=None):
    p = {"port": port, "targetPort": port, "name": "http"}
    if node:
        p["nodePort"] = node
    add("Service", name, {"selector": {"app": name}, "type": "NodePort" if node else "ClusterIP", "ports": [p]})


def deploy(name, image, port, memory, config=None, env=None, node=None, volumes=None, mounts=None, sa=False):
    c = {"name": name, "image": image, "ports": [{"containerPort": port}],
         "resources": {"requests": {"cpu": "100m", "memory": memory}, "limits": {"cpu": "2", "memory": memory}},
         "env": env or [], "volumeMounts": mounts or []}
    pod = {"containers": [c], "volumes": volumes or []}
    if config:
        c["env"] += [{"name": "SPRING_PROFILES_ACTIVE", "value": "local"}, {"name": "JAVA_OPTS", "value": "-XX:MaxRAMPercentage=65.0"}]
        c["envFrom"] = [{"secretRef": {"name": "spinnaker-local-secrets"}}]
        c["volumeMounts"].append({"name": "config", "mountPath": "/opt/spinnaker/config", "readOnly": True})
        pod["volumes"].append({"name": "config", "projected": {"sources": [{"configMap": {"name": "spinnaker-config"}}, {"configMap": {"name": name + "-config"}}]}})
        c["readinessProbe"] = {"httpGet": {"path": "/health", "port": port}, "periodSeconds": 10, "timeoutSeconds": 3}
    if sa:
        pod["serviceAccountName"] = "clouddriver"
    add("Deployment", name, {"replicas": 1, "selector": {"matchLabels": {"app": name}},
        "template": {"metadata": {"labels": {"app": name}}, "spec": pod}}, "apps/v1")
    service(name, port, node)


add("Namespace", "spinnaker", namespace=None)
add("Namespace", "sarseg-dev", namespace=None)
add("ServiceAccount", "clouddriver")
add("Role", "spinnaker-deployer", api="rbac.authorization.k8s.io/v1", namespace="sarseg-dev", rules=[
    {"apiGroups": ["", "apps", "autoscaling", "batch"], "resources": ["pods", "pods/log", "services", "configmaps", "deployments", "deployments/scale", "replicasets", "horizontalpodautoscalers", "jobs", "events"], "verbs": ["get", "list", "watch", "create", "update", "patch", "delete"]}])
add("RoleBinding", "spinnaker-deployer", api="rbac.authorization.k8s.io/v1", namespace="sarseg-dev",
    roleRef={"apiGroup": "rbac.authorization.k8s.io", "kind": "Role", "name": "spinnaker-deployer"}, subjects=[{"kind": "ServiceAccount", "name": "clouddriver", "namespace": "spinnaker"}])
add("ClusterRole", "spinnaker-local-discovery", api="rbac.authorization.k8s.io/v1", namespace=None, rules=[
    {"apiGroups": [""], "resources": ["namespaces", "nodes"], "verbs": ["get", "list", "watch"]},
    {"apiGroups": ["apiextensions.k8s.io"], "resources": ["customresourcedefinitions"], "verbs": ["get", "list"]}])
add("ClusterRoleBinding", "spinnaker-local-discovery", api="rbac.authorization.k8s.io/v1", namespace=None,
    roleRef={"apiGroup": "rbac.authorization.k8s.io", "kind": "ClusterRole", "name": "spinnaker-local-discovery"}, subjects=[{"kind": "ServiceAccount", "name": "clouddriver", "namespace": "spinnaker"}])

common = {"spring.config.import": "optional:file:/opt/spinnaker/config/*/", "services": {}}
for name, port in {"clouddriver": 7002, "front50": 8080, "orca": 8083, "gate": 8084}.items():
    common["services"][name] = {"baseUrl": f"http://{name}:{port}", "enabled": True}
for name in ["echo", "fiat", "igor", "kayenta", "keel", "rosco"]:
    common["services"][name] = {"enabled": False}
common["services"]["deck"] = {"baseUrl": "http://127.0.0.1:14900", "enabled": True}
add("ConfigMap", "spinnaker-config", data={"spinnaker.yml": yaml.safe_dump(common)})
for name in ["clouddriver", "front50", "orca", "gate"]:
    path = ROOT / "platform" / "config" / f"{name}-local.yml"
    add("ConfigMap", name + "-config", data={path.name: path.read_text(encoding="utf-8")})

init = '''#!/bin/sh
set -eu
for db in clouddriver front50 orca; do
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<SQL
CREATE DATABASE IF NOT EXISTS $db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${db}_service'@'%' IDENTIFIED BY '$SPIN_SQL_PASSWORD';
CREATE USER IF NOT EXISTS '${db}_migrate'@'%' IDENTIFIED BY '$SPIN_SQL_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, EXECUTE, SHOW VIEW ON $db.* TO '${db}_service'@'%';
GRANT ALL PRIVILEGES ON $db.* TO '${db}_migrate'@'%';
SQL
done
'''
add("ConfigMap", "mysql-init", data={"init.sh": init, "config.cnf": "[mysqld]\ntransaction_isolation=READ-COMMITTED\ninnodb_buffer_pool_size=128M\nmax_connections=160\n"})
for name in ["mysql", "redis"]:
    add("PersistentVolumeClaim", name + "-data", {"accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "1Gi"}}})
deploy("mysql", "mysql:8.0.45", 3306, "768Mi", env=[
    {"name": k, "valueFrom": {"secretKeyRef": {"name": "spinnaker-local-secrets", "key": k}}} for k in ["MYSQL_ROOT_PASSWORD", "SPIN_SQL_PASSWORD"]],
    volumes=[{"name": "data", "persistentVolumeClaim": {"claimName": "mysql-data"}}, {"name": "init", "configMap": {"name": "mysql-init", "defaultMode": 493}}],
    mounts=[{"name": "data", "mountPath": "/var/lib/mysql"}, {"name": "init", "mountPath": "/docker-entrypoint-initdb.d/init.sh", "subPath": "init.sh"}, {"name": "init", "mountPath": "/etc/mysql/conf.d/local.cnf", "subPath": "config.cnf"}])
deploy("redis", "redis:7.4.2-alpine", 6379, "128Mi", volumes=[{"name": "data", "persistentVolumeClaim": {"claimName": "redis-data"}}], mounts=[{"name": "data", "mountPath": "/data"}])
for name, port, mem, node in [("clouddriver", 7002, "1536Mi", None), ("front50", 8080, "768Mi", None), ("orca", 8083, "1536Mi", None), ("gate", 8084, "768Mi", 30884)]:
    deploy(name, f"ghcr.io/spinnaker/{name}:2026.4.1", port, mem, config=True, node=node, sa=name == "clouddriver")
settings = (ROOT / "platform/config/settings.js").read_text(encoding="utf-8")
add("ConfigMap", "deck-config", data={"settings.js": settings, "settings-local.js": "window.spinnakerSettings.authEnabled = false;\nwindow.spinnakerSettings.feature.kubernetesRawResources = true;\nwindow.spinnakerSettings.kubernetesAdHocInfraWritesEnabled = true;\n"})
deploy("deck", "ghcr.io/spinnaker/deck:2026.4.1", 9000, "192Mi", node=30900,
    env=[{"name": "DECK_HOST", "value": "0.0.0.0"}, {"name": "DECK_PORT", "value": "9000"}],
    volumes=[{"name": "config", "configMap": {"name": "deck-config"}}], mounts=[{"name": "config", "mountPath": "/opt/spinnaker/config", "readOnly": True}])
(ROOT / "platform/platform.yml").write_text(yaml.safe_dump_all(OUT, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"Generated {len(OUT)} Kubernetes resources")
