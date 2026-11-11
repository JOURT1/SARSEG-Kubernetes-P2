# Verificación de los entregables

## Informe

Se generó el PDF desde resultados de la ejecución final aprobada, sin completar
mediciones manualmente. Se renderizaron sus nueve páginas con Poppler y se
inspeccionaron visualmente. Se verificaron tres imágenes incrustadas y dieciséis
enlaces activos, incluido el enlace del repositorio público.

Los fragmentos de PowerShell se revisaron para conservar comillas y comandos
legibles. El informe diferencia exportaciones reales de la interfaz, registros
de terminal, resultados observados y usos futuros de SARSEG.

## Integridad de evidencias

Se comprobaron los cincuenta y cinco archivos indexados en SHA256SUMS.txt tanto
contra el contenido local como contra los blobs preparados para Git. Los textos
usan UTF8 y LF para obtener los mismos hashes en Windows y Linux.

## Ejecución

La ejecución final tiene once comprobaciones aprobadas y 113 de 113 solicitudes
HTTP correctas. La primera ejecución, con una conexión interrumpida, sigue
incluida. GitHub Actions ejecutó el mismo protocolo en un clúster independiente
y terminó correctamente; su enlace y SHA están en evidencias/github-actions.json.

El script Start-Lab.ps1 se volvió a ejecutar sobre el clúster existente para
validar que los manifiestos son aplicables de nuevo y que todos los Deployments
alcanzan su estado listo.

## Publicación

El repositorio de la práctica es público. Las cuatro ramas de avance y sus
commits se conservan después de integrar los pull requests. No se incluyen
kubeconfig, credenciales locales, herramientas descargadas ni código fuente
del repositorio privado SARSEG.
