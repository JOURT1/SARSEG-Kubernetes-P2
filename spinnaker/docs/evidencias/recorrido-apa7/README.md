# Recorrido documentado para el informe APA 7

El informe incluye **26 pasos, 26 figuras y 15 referencias**. Los archivos de
esta carpeta conservan los datos de cada paso y las imágenes originales.

- `pasos.json`: comandos, salidas, fuentes, clasificación y fecha de lectura.
- `01.html` a `26.html`: visores de registros o de archivos versionados.
- `capturas/paso-01.jpg` a `paso-26.jpg`: capturas originales del navegador.
- `encuadres.json`: región del visor utilizada al colocar la imagen en el PDF.
- `ejecucion-final-main.json`: resumen de Gate de la ejecución final de main.
- `SHA256SUMS.txt`: integridad de archivos, registros y capturas.

Las capturas 19 y 26 son lecturas directas de la aplicación y de GitHub.
La captura 21 conserva la interfaz nativa de Deck de la prueba original.
Las capturas 23 y 24 reutilizan los registros verificados del escalamiento
real de 2 a 5 y de regreso a 2 réplicas. Las demás muestran un visor documental
de salidas reales o archivos versionados, identificado como tal en la imagen.

La creación del clúster, compilación y despliegue ocurrieron durante la
implementación inicial. La lectura documental se realizó el 20 de noviembre
de 2026 (America/Guayaquil). No se presenta una lectura de configuración como
si fuera una nueva instalación, ni un registro histórico como un estado actual.

El generador PDF usa márgenes de 2,54 cm, Times New Roman 12, interlineado doble,
paginación superior, figuras numeradas con títulos en cursiva y notas de fuente,
y referencias con sangría francesa. El logotipo es una adaptación institucional
solicitada para la carátula estudiantil.

Para regenerar el informe a partir de las evidencias conservadas:

```powershell
python spinnaker/scripts/build_report.py
```

`collect_report_steps.py` realiza nuevas lecturas sin modificar el clúster;
se utiliza sólo al preparar un nuevo recorrido. Regenerar sus datos exige tomar
de nuevo las capturas para mantener la correspondencia entre registros e imágenes.
