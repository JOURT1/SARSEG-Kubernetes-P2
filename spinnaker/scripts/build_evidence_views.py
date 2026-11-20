"""Readable views of saved kubectl records; no new or simulated cluster data."""
import html
import json
from pathlib import Path
import yaml

E = Path(__file__).resolve().parents[1] / "docs/evidencias"
for key in ["01-inicial", "04-git-sincronizado", "05-carga-cinco", "06-reduccion-dos"]:
    record = json.loads((E / (key + ".json")).read_text(encoding="utf-8"))
    lines = record["blocks"][0]["output"].splitlines()
    deployment = next(x.split() for x in lines if x.startswith("deployment.apps/sarseg-web"))
    service = next(x.split() for x in lines if x.startswith("service/sarseg-web"))
    pods = [x.split() for x in lines if x.startswith("pod/sarseg-web-")]
    hpa = yaml.safe_load(record["blocks"][2]["output"])
    status, spec = hpa.get("status", {}), hpa["spec"]
    metrics = status.get("currentMetrics", [])
    cpu = next((str(x["resource"]["current"].get("averageUtilization", "—")) + "%" for x in metrics if x.get("resource",{}).get("name") == "cpu"), "Inicializando")
    rows = ''.join('<tr>' + ''.join('<td>' + html.escape(v) + '</td>' for v in [x[0].removeprefix('pod/'), x[1], x[2], x[3]]) + '</tr>' for x in pods)
    text = f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>{html.escape(record['title'])}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;padding:30px 40px;background:#f3f7fa;color:#112e45;font:19px Arial}}header{{font-size:15px;color:#267690;font-weight:bold;letter-spacing:2px}}h1{{font-size:31px;margin:12px 0}}p{{margin:8px 0;line-height:1.4}}.time{{font-size:14px;color:#577084}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:24px 0}}.card{{background:white;border:1px solid #d3dfe8;border-radius:9px;padding:18px}}.card span{{display:block;font-size:15px;color:#577084;margin-bottom:10px}}.card strong{{font-size:29px}}table{{width:100%;border-collapse:collapse;background:white;margin-top:16px;font-size:18px}}th{{background:#e1edf4;text-align:left}}th,td{{padding:12px 16px;border-bottom:1px solid #d4e0e9}}.meta{{display:flex;gap:35px;font-size:16px;margin:22px 0}}footer{{font-size:14px;border-top:1px solid #bed0dc;padding-top:14px;line-height:1.5}}code{{font:14px Consolas}}</style>
<header>SARSEG / SPINNAKER / KUBERNETES</header><h1>{html.escape(record['title'])}</h1>
<p>{html.escape(record['note'])}</p><p class="time">Registro UTC: {record['time']} · kind-sarseg-spinnaker · namespace sarseg-dev</p>
<div class="cards"><div class="card"><span>Deployment · Pods listos</span><strong>{deployment[1]}</strong></div>
<div class="card"><span>CPU observada / objetivo</span><strong>{cpu} / 50%</strong></div>
<div class="card"><span>HPA · mínimo / máximo</span><strong>{spec['minReplicas']} / {spec['maxReplicas']}</strong></div>
<div class="card"><span>Service · NodePort</span><strong>{service[4]}</strong></div></div>
<table><thead><tr><th>Pod de SARSEG web</th><th>Ready</th><th>Estado</th><th>Reinicios</th></tr></thead><tbody>{rows}</tbody></table>
<div class="meta"><span>Deployment: sarseg-web</span><span>HPA actual: {status.get('currentReplicas','—')}</span><span>HPA deseado: {status.get('desiredReplicas','—')}</span></div>
<footer>Visor resumido de un registro real; no es una interfaz nativa ni un estado en vivo.<br/>Fuente: <code>{key}.json</code>. Contiene los comandos y salidas completas de kubectl. No se altera el registro al generar este visor.</footer></html>'''
    (E / (key + ".compact.html")).write_text(text, encoding="utf-8")
print("Generated four evidence views from original JSON records")
