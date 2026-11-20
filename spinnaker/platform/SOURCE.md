La configuración parte del instalador mínimo oficial `spinnaker-kustomize`,
incluido en [Spinnaker 2026.4.1](https://github.com/spinnaker/spinnaker/tree/1b3ed435fe5341b41dcbbdce999cb771145166a8/spinnaker-kustomize).
Se conservan la licencia Apache 2.0 y las configuraciones SQL y Deck adaptadas.

Se ejecutan Deck, Gate, Orca, Clouddriver y Front50; MySQL conserva las
aplicaciones y ejecuciones y Redis administra la cola. No se necesita Rosco
porque no se hornean imágenes ni plantillas. El sondeo Git local inicia Orca
por Gate y sustituye el webhook externo; no se ejecuta Echo.

`scripts/build_platform.py` regenera `platform.yml` sin credenciales. Los Secret
se generan localmente por `scripts/bootstrap.py`. Los permisos de despliegue de
Clouddriver se limitan al namespace `sarseg-dev`.
