# Verificación de los entregables

## Informe

Se generó el PDF ampliado desde los resultados de la reproducción aprobada,
conservando por separado las ejecuciones originales. Se renderizaron sus treinta
y seis páginas con Poppler para la inspección visual. Contiene veintiséis figuras
del recorrido, veintisiete imágenes incrustadas contando el logotipo, catorce
enlaces activos y cuarenta y tres marcadores de navegación.

La portada incluye el enlace completo y clicable del repositorio público.

Se comprobó tamaño carta en todas las páginas, márgenes de 2,54 cm, Times New
Roman 12, interlineado doble, sangría inicial, numeración superior derecha,
figuras con número y título, citas autor-fecha y referencias con sangría francesa.
Las tablas usan reglas horizontales y un tamaño de texto adecuado a su contenido.
El logotipo oficial es una adaptación institucional de la carátula solicitada.

El informe diferencia capturas directas de GitHub y Grafana, capturas del visor
de registros, exportaciones de la plataforma, resultados observados y usos
futuros. Se revisó la legibilidad de las capturas y se corrigieron tres imágenes
antes de incorporarlas al PDF definitivo.

## Integridad de evidencias

Se comprobaron los ciento nueve archivos indexados en SHA256SUMS.txt tanto
contra el contenido local como contra los blobs preparados para Git. Los textos
usan UTF8 y LF para obtener los mismos hashes en Windows y Linux.

## Ejecución

La ejecución original final tiene once comprobaciones aprobadas y 113 de 113
solicitudes HTTP correctas. La reproducción desde cero del recorrido amplió la
evidencia con once comprobaciones y 109 de 109 muestras correctas. La primera
ejecución original, con una conexión interrumpida, sigue incluida. Los contextos,
los puertos y los UIDs identifican cada ejecución. GitHub Actions también ejecutó
el protocolo en un clúster independiente y terminó correctamente.

El script Start-Lab.ps1 se volvió a ejecutar sobre el clúster existente para
validar que los manifiestos son aplicables de nuevo y que todos los Deployments
alcanzan su estado listo.

## Publicación

El repositorio de la práctica es público. Las cuatro ramas de avance y sus
commits se conservan después de integrar los pull requests. No se incluyen
kubeconfig, credenciales locales, herramientas descargadas ni código fuente
del repositorio privado SARSEG.
