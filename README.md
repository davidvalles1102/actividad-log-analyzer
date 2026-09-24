# Analizador de logs — Actividad Individual

**Repositorio:** https://github.com/davidvalles1102/actividad-log-analyzer

Script en Python que analiza un archivo de texto con eventos de log (`[INFO]`, `[WARNING]`, `[ERROR]`, con o sin fecha) y muestra en consola un resumen: total de eventos, cantidad por tipo de severidad, líneas con y sin fecha válida, y líneas mal formateadas.

## Contenido de la carpeta

- `log_analyzer.py` — script principal.
- `pruebas/logs_bien_formados.txt` — caso de prueba sin errores.
- `pruebas/logs_con_errores.txt` — caso de prueba con líneas inválidas a propósito.
- `REFLEXION_TECNICA.md` — documento de reflexión: qué apoyó la IA, qué decisiones se tomaron, ejemplo de corrección a una sugerencia de la IA, y descripción de las pruebas.

## Cómo ejecutarlo

Requiere Python 3 (sin librerías externas).

```bash
python log_analyzer.py pruebas/logs_bien_formados.txt
python log_analyzer.py pruebas/logs_con_errores.txt
```

También se puede ejecutar sin argumentos; el script pide la ruta por consola:

```bash
python log_analyzer.py
```

## Resultados esperados

**`logs_bien_formados.txt`:** 10 eventos, 0 mal formateadas, 9 con fecha válida / 1 sin fecha válida, 4 INFO / 3 WARNING / 3 ERROR.

**`logs_con_errores.txt`:** 9 eventos, 3 mal formateadas, 3 con fecha válida / 4 sin fecha válida, 2 INFO / 2 WARNING / 3 ERROR.

El detalle de por qué se definieron así las reglas de validación, y un ejemplo concreto de una sugerencia incorrecta de la IA que fue detectada y corregida, está en `REFLEXION_TECNICA.md`.
