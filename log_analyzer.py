"""
Analizador de logs de eventos de una aplicacion.

Actividad: "IA como Herramienta, no como Autor" - Desarrollo Guiado y Validado
de un Script en Python.

Autor: Evelyn Hernandez
Apoyo de IA: Claude (Anthropic), usado para proponer expresiones regulares y
la estructura inicial de funciones. Las reglas de validacion (que cuenta como
linea invalida, que hacer con la fecha, que casos borde se cubren) fueron
decididas por la autora; el detalle de cada decision esta documentado en los
comentarios de este archivo y en el documento de reflexion tecnica.
"""

import sys
import os
from datetime import datetime
import re

# Unicamente se aceptan estos tres niveles de severidad. Cualquier otra
# palabra entre corchetes (o su ausencia) se trata como linea mal formateada.
SEVERIDADES_VALIDAS = {"INFO", "WARNING", "ERROR"}

# Regex para capturar la etiqueta de severidad al inicio de la linea, sea cual
# sea su capitalizacion (ej. "[info]", "[Info]", "[INFO]" se aceptan todas;
# la normalizacion a mayusculas es una decision propia para no penalizar un
# simple descuido de tipeo del generador del log, no un error de contenido).
PATRON_SEVERIDAD = re.compile(r"^\s*\[([A-Za-z]+)\]\s*(.*)$")

# Regex para localizar un posible token de fecha en formato AAAA-MM-DD dentro
# del resto de la linea. Ojo: este patron SOLO valida el formato (cuantos
# digitos y en que posicion), no si la fecha realmente existe en el
# calendario. Esa segunda verificacion se hace aparte con datetime.strptime,
# porque la primera version de este regex (sugerida por la IA) fue aceptada
# sin ese control y dejaba pasar fechas invalidas como "2025-13-40"
# (ver documento de reflexion tecnica, seccion "Ejemplo de correccion a la IA").
PATRON_FECHA = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def evaluar_fecha(token_fecha):
    """
    Recibe el texto que hace match con PATRON_FECHA y confirma si corresponde
    a una fecha real usando datetime.strptime (por ejemplo, "2025-02-30" o
    "2025-13-01" tienen el formato correcto pero no son fechas validas).

    Decision propia: si la fecha tiene el formato correcto pero el valor no
    existe en el calendario, se considera "sin fecha valida", igual que si
    no hubiera ninguna fecha en la linea. No se distingue entre ambos casos
    en el resumen final porque, para el objetivo de esta actividad, lo que
    importa es si se puede confiar en la fecha del evento o no.
    """
    try:
        datetime.strptime(token_fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def analizar_linea(linea, numero_linea):
    """
    Analiza una sola linea del log y devuelve un diccionario con:
      - numero: numero de linea (para poder ubicarla en el archivo original)
      - severidad: "INFO" / "WARNING" / "ERROR" / None
      - tiene_fecha_valida: True / False
      - mensaje: texto del evento (puede quedar vacio)
      - mal_formateada: True / False
      - motivo: texto corto que explica por que se marco como mal formateada
                (cadena vacia si la linea esta bien)

    Decision propia clave: segun el enunciado, una linea como
    "[WARNING] Invalid password attempt" (sin fecha) es un ejemplo VALIDO de
    log, no un error. Por lo tanto la ausencia de fecha NO cuenta como linea
    mal formateada; se cuenta aparte en "lineas sin fecha valida". Solo se
    marca como mal formateada cuando la estructura minima del evento falla:
    no se reconoce la etiqueta de severidad, la etiqueta no es una de las
    tres permitidas, o no queda ningun mensaje despues de quitar la etiqueta
    (y la fecha, si la hubiera).
    """
    resultado = {
        "numero": numero_linea,
        "severidad": None,
        "tiene_fecha_valida": False,
        "mensaje": "",
        "mal_formateada": False,
        "motivo": "",
    }

    match_severidad = PATRON_SEVERIDAD.match(linea)
    if not match_severidad:
        resultado["mal_formateada"] = True
        resultado["motivo"] = "no se encontro una etiqueta de severidad entre corchetes al inicio"
        resultado["mensaje"] = linea.strip()
        return resultado

    etiqueta_cruda, resto = match_severidad.groups()
    etiqueta = etiqueta_cruda.upper()
    resto = resto.strip()

    if etiqueta not in SEVERIDADES_VALIDAS:
        resultado["mal_formateada"] = True
        resultado["motivo"] = f"severidad desconocida: '{etiqueta_cruda}'"
        resultado["mensaje"] = resto
        return resultado

    resultado["severidad"] = etiqueta

    # Buscar una fecha dentro del resto de la linea y separarla del mensaje.
    match_fecha = PATRON_FECHA.search(resto)
    mensaje = resto
    if match_fecha:
        token_fecha = match_fecha.group(1)
        resultado["tiene_fecha_valida"] = evaluar_fecha(token_fecha)
        # Se quita el token de fecha del texto para dejar el mensaje limpio,
        # sin importar si la fecha resulto valida o no (si no es valida, de
        # todas formas no aporta como mensaje del evento).
        mensaje = (resto[: match_fecha.start()] + resto[match_fecha.end():]).strip()

    resultado["mensaje"] = mensaje

    if not mensaje:
        resultado["mal_formateada"] = True
        resultado["motivo"] = "no quedo mensaje despues de quitar severidad y fecha"

    return resultado


def analizar_archivo(ruta):
    """
    Lee el archivo linea por linea y devuelve la lista de resultados de
    analizar_linea() para cada linea no vacia.

    Decision propia: las lineas completamente en blanco (o solo con espacios)
    se ignoran por completo, no se cuentan ni como evento ni como linea mal
    formateada. Un log real puede tener lineas en blanco por formato del
    archivo y contarlas como "evento" o "error" distorsionaria el resumen.
    """
    resultados = []
    with open(ruta, "r", encoding="utf-8", errors="strict") as archivo:
        for numero_linea, linea_cruda in enumerate(archivo, start=1):
            linea = linea_cruda.rstrip("\n").rstrip("\r")
            if not linea.strip():
                continue
            resultados.append(analizar_linea(linea, numero_linea))
    return resultados


def construir_resumen(resultados):
    """Agrupa los resultados por linea en los contadores del resumen final."""
    resumen = {
        "total_eventos": len(resultados),
        "por_severidad": {"INFO": 0, "WARNING": 0, "ERROR": 0},
        "mal_formateadas": 0,
        "con_fecha_valida": 0,
        "sin_fecha_valida": 0,
    }

    for r in resultados:
        if r["severidad"] is not None:
            resumen["por_severidad"][r["severidad"]] += 1

        if r["mal_formateada"]:
            resumen["mal_formateadas"] += 1

        # La fecha se reporta para toda linea que si tiene severidad
        # reconocida, sin importar si esta mal formateada por otro motivo
        # (ej. mensaje vacio). Si no hay severidad reconocida, la linea ya
        # esta descartada como estructura y no tiene sentido evaluarle fecha.
        if r["severidad"] is not None:
            if r["tiene_fecha_valida"]:
                resumen["con_fecha_valida"] += 1
            else:
                resumen["sin_fecha_valida"] += 1

    return resumen


def imprimir_reporte(ruta, resultados, resumen):
    print("=" * 60)
    print(f"REPORTE DE ANALISIS DE LOG: {ruta}")
    print("=" * 60)

    print("\nDetalle por linea:")
    print("-" * 60)
    for r in resultados:
        estado = "OK" if not r["mal_formateada"] else "MAL FORMATEADA"
        severidad = r["severidad"] if r["severidad"] else "SIN SEVERIDAD"
        fecha = "con fecha valida" if r["tiene_fecha_valida"] else "sin fecha valida"
        linea_info = f"L{r['numero']:>4} | {severidad:<14} | {fecha:<17} | {estado}"
        if r["mal_formateada"]:
            linea_info += f" ({r['motivo']})"
        print(linea_info)

    print("\nResumen")
    print("-" * 60)
    print(f"Total de eventos analizados : {resumen['total_eventos']}")
    print(f"  - INFO                    : {resumen['por_severidad']['INFO']}")
    print(f"  - WARNING                 : {resumen['por_severidad']['WARNING']}")
    print(f"  - ERROR                   : {resumen['por_severidad']['ERROR']}")
    print(f"Lineas con fecha valida     : {resumen['con_fecha_valida']}")
    print(f"Lineas sin fecha valida     : {resumen['sin_fecha_valida']}")
    print(f"Lineas mal formateadas      : {resumen['mal_formateadas']}")
    print("=" * 60)


def pedir_ruta_archivo():
    """
    Pide al usuario la ruta del archivo a analizar.

    Decision propia: se usa una ruta por consola (input) en lugar de un
    selector grafico (tkinter). Un dialogo grafico depende de que haya
    entorno de escritorio disponible y complica probar el script desde una
    terminal o en un entorno de evaluacion automatizada; pedir la ruta por
    consola (o como argumento de linea de comandos) funciona siempre.
    Se permite tambien pasar la ruta como argumento: python log_analyzer.py archivo.txt
    """
    if len(sys.argv) > 1:
        return sys.argv[1]

    while True:
        ruta = input("Ruta del archivo de log a analizar: ").strip().strip('"')
        if os.path.isfile(ruta):
            return ruta
        print(f"No se encontro el archivo '{ruta}'. Intenta de nuevo (Ctrl+C para salir).")


def main():
    ruta = pedir_ruta_archivo()

    try:
        resultados = analizar_archivo(ruta)
    except FileNotFoundError:
        print(f"Error: no se encontro el archivo '{ruta}'.")
        sys.exit(1)
    except UnicodeDecodeError:
        print(
            f"Error: '{ruta}' no se pudo leer como texto UTF-8. "
            "Verifica la codificacion del archivo."
        )
        sys.exit(1)
    except PermissionError:
        print(f"Error: no hay permisos para leer '{ruta}'.")
        sys.exit(1)

    if not resultados:
        print(f"El archivo '{ruta}' no tiene lineas con contenido para analizar.")
        return

    resumen = construir_resumen(resultados)
    imprimir_reporte(ruta, resultados, resumen)


if __name__ == "__main__":
    main()
