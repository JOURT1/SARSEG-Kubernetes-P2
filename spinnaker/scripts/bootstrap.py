"""Install infrastructure and generate local-only secrets through stdin."""
import base64
import json
import secrets
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT.parent / ".local" / "spinnaker"
CTX = "kind-sarseg-spinnaker"


def kubectl(*args, data=None):
    return subprocess.run(["kubectl", "--context", CTX, *args], input=data, text=True, check=True, capture_output=True).stdout


def main():
    LOCAL.mkdir(parents=True, exist_ok=True)
    path = LOCAL / "credentials.json"
    if path.exists():
        values = json.loads(path.read_text())
    else:
        values = {"MYSQL_ROOT_PASSWORD": secrets.token_hex(24), "SPIN_SQL_PASSWORD": secrets.token_hex(24),
                  "POSTGRES_PASSWORD": secrets.token_hex(24), "ADMIN_PASSWORD": secrets.token_urlsafe(20),
                  "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(), "PIN_PEPPER": secrets.token_hex(32)}
        path.write_text(json.dumps(values, indent=2))
    for ns in ["spinnaker", "sarseg-dev"]:
        kubectl("apply", "-f", "-", data=json.dumps({"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": ns}}))
    for name, ns, data in [
        ("spinnaker-local-secrets", "spinnaker", {k: values[k] for k in ["MYSQL_ROOT_PASSWORD", "SPIN_SQL_PASSWORD"]}),
        ("sarseg-local-secrets", "sarseg-dev", {
            "POSTGRES_PASSWORD": values["POSTGRES_PASSWORD"],
            "ConnectionStrings__Database": "Host=postgres;Database=sarseg;Username=sarseg;Password=" + values["POSTGRES_PASSWORD"],
            "Security__EncryptionKey": values["ENCRYPTION_KEY"], "Security__PinPepper": values["PIN_PEPPER"],
            "Bootstrap__Username": "admin", "Bootstrap__Password": values["ADMIN_PASSWORD"]})]:
        kubectl("apply", "-f", "-", data=json.dumps({"apiVersion": "v1", "kind": "Secret", "metadata": {"name": name, "namespace": ns}, "stringData": data}))
    print(kubectl("apply", "-f", str(ROOT / "platform/platform.yml")))
    print(kubectl("apply", "-f", str(ROOT / "platform/metrics-server.yml")))
    print("Credenciales conservadas en .local/spinnaker/credentials.json (fuera de Git).")


if __name__ == "__main__":
    main()
