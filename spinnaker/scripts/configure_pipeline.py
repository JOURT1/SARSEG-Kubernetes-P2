"""Save the application and artifact-based deployment pipeline through Gate."""
import json
import time
from pathlib import Path
from git_watch import request, FILES

ROOT = Path(__file__).resolve().parents[1]


def definition():
    stages = []
    for index, name in enumerate(FILES, 1):
        key = name.removesuffix(".yml")
        stages.append({"refId": str(index), "requisiteStageRefIds": [] if index == 1 else [str(index - 1)],
            "name": "Deploy " + name, "type": "deployManifest", "account": "sarseg-local", "cloudProvider": "kubernetes",
            "namespaceOverride": "sarseg-dev", "source": "artifact",
            "manifestArtifact": {"type": "http/file", "name": name, "artifactAccount": "public-git-http",
                "reference": "https://raw.githubusercontent.com/JOURT1/SARSEG-Kubernetes-P2/${parameters.gitSha}/spinnaker/k8s/" + name},
            "manifestArtifactAccount": "public-git-http", "moniker": {"app": "sarseg"}, "skipExpressionEvaluation": False,
            "stageTimeoutMs": 300000, "trafficManagement": {"enabled": False, "options": {"enableTraffic": True}}})
    return {"id": "sarseg-deploy-git", "application": "sarseg", "name": "deploy-git", "keepWaitingPipelines": False,
            "limitConcurrent": True, "triggers": [], "stages": stages,
            "parameterConfig": [{"name": "gitSha", "required": True}, {"name": "gitBranch", "required": True}],
            "description": "Git public -> immutable SHA HTTP artifacts -> Spinnaker -> SARSEG Kubernetes local"}


if __name__ == "__main__":
    pipeline = definition()
    (ROOT / "pipeline.json").write_text(json.dumps(pipeline, indent=2) + "\n")
    applications = request("/applications")
    if not any(a.get("name") == "sarseg" for a in applications):
        task = request("/tasks", {"application": "sarseg", "description": "Create SARSEG local application",
            "job": [{"type": "createApplication", "application": {"name": "sarseg", "email": "jhoel.suarez@udla.edu.ec",
                "cloudProviders": "kubernetes", "description": "SARSEG: despliegue GitOps local con Spinnaker"}}]})
        for _ in range(60):
            result = request(task["ref"])
            if result.get("status") == "SUCCEEDED":
                break
            if result.get("status") in ["TERMINAL", "CANCELED"]:
                raise RuntimeError("Application creation failed: " + json.dumps(result))
            time.sleep(2)
        else:
            raise TimeoutError("Application creation timed out")
    request("/pipelines", pipeline)
    print("Application sarseg and pipeline deploy-git saved through Gate")
