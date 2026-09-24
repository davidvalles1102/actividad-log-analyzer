# Reflexión técnica — Analizador de logs

**Actividad:** IA como Herramienta, no como Autor
**Autora:** Evelyn Hernández

## 1. Qué partes del código apoyó la IA

Usé Claude (integrado en VS Code) en tres momentos puntuales, no para escribir el script de principio a fin:

- Para proponer el primer borrador de la expresión regular que separa la etiqueta de severidad (`[INFO]`, `[WARNING]`, `[ERROR]`) del resto de la línea.
- Para sugerir una expresión regular que detectara un token con forma de fecha `AAAA-MM-DD` dentro del texto.
- Para armar el esqueleto de manejo de excepciones al abrir el archivo (`FileNotFoundError`, `UnicodeDecodeError`, `PermissionError`), que yo después adapté a los mensajes y al flujo que quería.

En los tres casos partí de lo que la IA propuso, pero terminé reescribiendo la lógica alrededor una vez que probé el script con casos que no venían en el ejemplo del enunciado.

## 2. Qué decidí yo

El enunciado es explícito en que la IA no puede definir las reglas de validación, así que estas decisiones las tomé revisando el propio ejemplo del enunciado y pensando en cómo se comportaría un log real:

**Que falte la fecha no es un error.** El enunciado da como ejemplo válido `[WARNING] Invalid password attempt`, sin fecha. Si hubiera tratado cualquier línea sin fecha como "mal formateada", ese mismo ejemplo del enunciado habría contado como error, lo cual no tiene sentido. Por eso separé dos cosas que la IA tendía a mezclar en una sola idea de "línea con problema": (a) si la línea tiene fecha válida o no, que se reporta aparte, y (b) si la línea está mal formateada, que se reserva para fallas de estructura reales.

**Qué cuenta como "mal formateada".** Definí solo tres motivos: no encontrar ninguna etiqueta entre corchetes al inicio de la línea, encontrar una etiqueta que no sea INFO/WARNING/ERROR, o que no quede ningún mensaje después de quitar etiqueta y fecha. Cualquier otra cosa —incluida la ausencia de fecha— se considera un evento válido, aunque incompleto en ese dato puntual.

**Severidad en minúsculas.** Decidí aceptar `[warning]` o `[error]` normalizando a mayúsculas antes de comparar, porque es un descuido de formato, no un problema de contenido del evento. Es una decisión discutible —alguien podría argumentar que debería marcarse como advertencia de formato— pero la documenté en el propio código (`log_analyzer.py`, función `analizar_linea`) para que quede claro que fue elegida a propósito y no un olvido.

**Líneas en blanco.** Se ignoran por completo: no cuentan como evento ni como error. Un archivo de log real casi siempre tiene alguna línea vacía por cómo se generó, y contarla distorsionaría el resumen sin aportar información real sobre el sistema que generó el log.

**Lo que dejé fuera a propósito.** No intento reconocer fechas en otro formato que no sea `AAAA-MM-DD`, no valido la hora si viene junto a la fecha, y no manejo más de una fecha por línea (si hay dos, tomo la primera). Son casos que podrían darse en un log real, pero ampliarlos habría significado adivinar reglas que el enunciado no pide, y preferí ser explícita sobre el límite en vez de inventar un comportamiento no solicitado.

## 3. Un caso donde la IA se equivocó y lo corregí

La expresión regular que Claude propuso primero para las fechas fue esta:

```python
PATRON_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")
```

Funciona para el ejemplo del enunciado, pero solo valida la *forma* del texto, no si la fecha existe. Lo noté al construir el archivo de prueba con errores: escribí a propósito la línea `[ERROR] 2025-13-40 Invalid date but format looks right`, y con esa regex el script la marcaba como "fecha válida" porque cuatro dígitos, guion, dos dígitos, guion, dos dígitos es justo lo que el patrón pide. El mes 13 y el día 40 no existen, pero la regex no tiene forma de saberlo.

La corrección fue agregar una segunda verificación con `datetime.strptime(token, "%Y-%m-%d")` dentro de un `try/except ValueError` (función `evaluar_fecha` en el script). Ahora la regex solo localiza el candidato a fecha, y `strptime` decide si es real. Con ese cambio, tanto `2025-13-40` como `2025-02-30` (30 de febrero, que tampoco existe) quedan correctamente marcadas como "sin fecha válida" al correr el script contra `pruebas/logs_con_errores.txt`.

## 4. Qué aprendí sobre usar IA como herramienta

Lo que más se repitió durante esta actividad es que la IA resuelve bien la sintaxis pero no tiene manera de saber qué decisión de negocio quiero tomar si yo no se la doy explícita. La regex de fecha no estaba "mal escrita" en el sentido de que hiciera lo que se le pidió; el problema es que "detectar una fecha" y "confirmar que es una fecha real" son dos problemas distintos, y hasta que yo no planteé esa distinción, la IA resolvió el que le pareció más obvio. Pasó algo parecido con la definición de "línea mal formateada": si le hubiera preguntado a la IA "¿cómo detecto una línea inválida?" sin darle el criterio de que la ausencia de fecha es válida según el propio enunciado, probablemente habría propuesto marcar como error cualquier línea sin fecha, contradiciendo el ejemplo del enunciado.

Encontrar el error de la fecha implicó escribir primero los casos de prueba con datos que sabía que iban a estresar el límite de la regla (una fecha con formato correcto pero valor imposible), no solo revisar el código a simple vista. Ese fue el momento donde se hizo evidente para mí: la IA no valida sus propias sugerencias contra casos borde a menos que se le pidan explícitamente, así que esa responsabilidad quedó de mi lado en todo momento.

## 5. Evidencia de pruebas

### Archivo 1: `pruebas/logs_bien_formados.txt`

Diez líneas, todas con etiqueta de severidad reconocida y mensaje. Incluye a propósito una línea sin fecha (`[WARNING] Invalid password attempt`, tal como el ejemplo del enunciado) y una etiqueta en minúsculas (`[warning]`) para confirmar que ninguna de las dos se marca como error.

**Resultado esperado:** 10 eventos totales, 0 líneas mal formateadas, 9 con fecha válida y 1 sin fecha válida (la línea de `WARNING` sin fecha), 4 INFO / 3 WARNING / 3 ERROR.

**Resultado obtenido:** coincide exactamente con lo esperado al ejecutar `python log_analyzer.py pruebas/logs_bien_formados.txt`.

### Archivo 2: `pruebas/logs_con_errores.txt`

Once líneas pensadas para forzar cada regla de validación por separado: una línea sin corchetes (`ERROR Failed to connect to database`), una línea en blanco, una con severidad no reconocida (`[DEBUG]`), una fecha con formato correcto pero mes imposible (`2025-13-40`), otra con día imposible (`2025-02-30`), una etiqueta sola sin mensaje (`[INFO]`), una línea con solo espacios en blanco, y una etiqueta en minúsculas para confirmar que sigue contando.

**Resultado esperado:** 9 eventos (las 2 líneas en blanco/con solo espacios no cuentan), 3 líneas mal formateadas (la de `ERROR` sin corchetes, la de `[DEBUG]`, y la de `[INFO]` sin mensaje), 3 con fecha válida y 4 sin fecha válida, 2 INFO / 2 WARNING / 3 ERROR.

**Resultado obtenido:** coincide exactamente con lo esperado al ejecutar `python log_analyzer.py pruebas/logs_con_errores.txt`. El detalle línea por línea que imprime el script (número de línea, severidad, estado de la fecha y motivo cuando está mal formateada) permitió confirmar cada caso de forma individual, no solo los totales del resumen.

### Casos adicionales probados fuera de los dos archivos anteriores

Además de los dos archivos de prueba, ejecuté el script contra dos situaciones que no son errores de contenido dentro del log sino errores de uso del programa: pedirle un archivo que no existe (`python log_analyzer.py no_existe.txt`) y pasarle un archivo vacío. En el primer caso el script responde `Error: no se encontro el archivo 'no_existe.txt'.` y termina sin quebrarse; en el segundo, responde `El archivo 'pruebas/vacio.txt' no tiene lineas con contenido para analizar.` en vez de mostrar un resumen con ceros que podría confundirse con "0 errores encontrados". Ambos casos están cubiertos explícitamente en el código (bloque `try/except` de `main()` y la verificación `if not resultados` antes de construir el resumen).
