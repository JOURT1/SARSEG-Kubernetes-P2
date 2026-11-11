# Hallazgos durante la validación

## Reparto entre nodos

Durante el primer cambio de plantilla, el scheduler dejó un Pod Pending porque
la restricción de reparto contaba el dominio del control plane, que no admitía
esa carga. Se agregó afinidad obligatoria que excluye nodos con la etiqueta
node-role.kubernetes.io/control-plane. Se comprobó el despliegue en ambos workers.

## Conexión interrumpida durante el primer rollout

La primera ejecución completa pasó escalado, reposición y rollback, pero obtuvo
110 respuestas correctas de 111 muestras HTTP. La muestra de
2026-11-11T05:02:42.161Z registró RemoteDisconnected durante el rollout. El script
marcó success=false; los registros se conservan en evidencias/ejecucion.

El evento es compatible con una carrera entre la retirada del endpoint y la
terminación del proceso. No se atribuye una causa única sin una traza de red.
Se añadió preStop de diez segundos y un periodo de gracia de treinta segundos
para permitir drenaje. La ejecución de comprobación se conserva por separado
en evidencias/ejecucion-final, sin borrar el primer resultado.

Las advertencias iniciales de startupProbe con conexión rechazada corresponden
al arranque previo a que Grafana abra el puerto. Se verifica Ready y rollout
completo antes de declarar la plataforma disponible.
