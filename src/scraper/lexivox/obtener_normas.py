"""
Abogashon. (C) Rodrigo Garcia 2026
"""

import json
import random
import os
import requests
import time
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# -------------- utils ------------------

def guardar_progreso(nuevos_datos, nombre_archivo="datos.json"):
    # 1. Si el archivo ya existe, leer su contenido
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            try:
                lista_existente = json.load(f)
            except json.JSONDecodeError:
                lista_existente = [] # Por si el archivo está vacío
    else:
        lista_existente = []

    # 2. Agregar las nuevas entradas a la lista
    lista_existente.extend(nuevos_datos)

    # 3. Guardar la lista actualizada
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(lista_existente, f, ensure_ascii=False, indent=4)



def limpiar_nombre(texto):
    return texto.lower().replace(" ", "-").replace("/", "-")

# -------------- main -----------------


# actualizar
archivo_metadata = '../../../normas/24-abril-metadata.json'

with open(archivo_metadata, 'r', encoding='utf-8') as f:
    normas = json.load(f)

# Iterar sobre las entradas
for norma in normas:
    url = norma['enlaceNorma']
    anio = norma['MM/AAAA'].split('/')[-1]  # Extrae '1990'
    nombre_base = limpiar_nombre(norma['nombre'])
    
    # Crear ruta de carpeta: normas/1990
    ruta_carpeta = os.path.join("..", "..", "..", "normas", anio)
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)
    
    ruta_archivo = os.path.join(ruta_carpeta, f"{nombre_base}.md")

    # Saltar si ya existe (útil si el proceso se interrumpe)
    if os.path.exists(ruta_archivo):
        print(f'Ya existe {ruta_archivo}')
        continue

    try:
        # 4. Obtener HTML y procesar
        print(f"Ingresando a {url}")
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8' # Asegurar tildes
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Seleccionar la sección específica
        seccion_norma = soup.select_one('#normTxtId')
        
        if seccion_norma:
            # 5. Convertir a Markdown
            contenido_md = md(str(seccion_norma), heading_style="ATX")
            
            # 6. Guardar archivo
            with open(ruta_archivo, "w", encoding="utf-8") as f_md:
                f_md.write(contenido_md)
            
            print(f"Guardado: {ruta_archivo}")
        else:
            print(f"No se encontró el ID en: {url}")

        # 7. Delay de cortesía para no saturar el servidor
        pausa = random.randint(1, 2)
        print(f'Pausa {pausa} segundos...')
        time.sleep(pausa)

    except Exception as e:
        print(f"Error procesando {url}: {e}")
