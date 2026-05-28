"""
Abogacion. (C) Rodrigo Garcia 2026
"""

"""
Buscar por rango de fechas
http://www.gacetaoficialdebolivia.gob.bo/normas/buscarFecha/2025-11-09/2026-12-12

Formato: AAAA-DD-MM
"""
import asyncclick as click
import json
import os
import random
import re
import requests
import time
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from src.scraper.common.selectors import get_selector_value, get_locator, get_all_elements_from_locator
from src.scraper.common.utils import obtener_nombre_desde_contenido, FUENTE_GACETA, FUENTE_LEXIVOX, ARCHIVO_ABROGADAS
from src.common.custom_logger import CustomLogger
from src.common.time import random_sleep, today_yyyymmdd, age_in_days, datetime_from_yyyymmdd, mes_from_number



LOGGER = CustomLogger('gaceta - metadata ')

selectors = {
    "lista de normas": {
        "título": {
            "value": "//div[@id='main_content']//div[@class='row']//h6",
            "stype": "xpath"
        },
        'código': {
            "value": "//div[@class='row']//div[@class='card-body']//p[contains(text(), 'Publicado en')]/strong/a",
            "stype": "xpath"
        },
        "cabecera meta": {
            "value": "//div[@class='row']//div[@class='card-body']//p[contains(text(), 'Publicado en')]",
            # para obtener la fecha de publicación hay que filtrar el texto entre '| Fecha de Publicación: <fecha> |'
            #  | Fecha de Publicación: 2025-11-09 |  Formato de fecha YYYY-MM-DD
            "stype": "xpath"
        },
        "enlace": {
            "value": "//div[@class='row']//div[@class='card-footer bg-transparent text-end']/a[text()='Ver Norma']",
            "stype": "xpath"
        },
        "botón siguiente": {
            "value": "//div[@class='paging']/a[not(@class='disabled')][text()='siguiente >>']",
            "stype": "xpath"
        }
    },
    "normas": {
        "contenido": {
            "value": "//div[@id='seleccion']",
            "stype": "xpath"
        }
    }
}

# -------------------------------- utils --------------------------------------------

def guardar_progreso(nuevos_datos, nombre_archivo="datos.json"):
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            try:
                lista_existente = json.load(f)
            except json.JSONDecodeError:
                lista_existente = [] # Por si el archivo está vacío
    else:
        lista_existente = []

    lista_existente.extend(nuevos_datos)

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(lista_existente, f, ensure_ascii=False, indent=4)


def obtener_archivo_metadata_mas_reciente(directorio: str = "normas") -> Path | None:
    """
    Retorna el Path del archivo JSON más reciente en el directorio dado,
    basado en la fecha contenida en el nombre del archivo.

    El nombre debe seguir el patrón: YYYY-MM-DD_gaceta_metadata.json

    Args:
        directorio (str): Ruta al directorio donde se buscan los archivos.
                          Por defecto "normas".

    Returns:
        Path | None: Path del archivo más reciente, o None si no se encuentra
                     ningún archivo válido o el directorio no existe.
    """
    ruta_dir = Path(directorio)
    if not ruta_dir.is_dir():
        print(f"El directorio '{directorio}' no existe.")
        return None

    # Patrón para validar y extraer la fecha del nombre
    patron = re.compile(r'^(\d{4}-\d{2}-\d{2})_gaceta_metadata\.json$')

    archivos_validos = []
    for archivo in ruta_dir.glob("*.json"):
        coincidencia = patron.match(archivo.name)
        if coincidencia:
            fecha_str = coincidencia.group(1)
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                archivos_validos.append((fecha, archivo))
            except ValueError:
                # Si la fecha no es válida, ignorar el archivo
                continue

    if not archivos_validos:
        print("No se encontraron archivos con el formato esperado.")
        return None

    # Obtener el archivo con la fecha más reciente
    fecha_max, archivo_reciente = max(archivos_validos, key=lambda x: x[0])
    return archivo_reciente
    

def limpiar_nombre(texto):
    return texto.lower().replace(" ", "-").replace("/", "-")

# ---------------------------- funciones principales ----------------------------------------

async def obtener_metadata(desde_fecha, hasta_fecha):
    from_date = datetime_from_yyyymmdd(desde_fecha).strftime('%Y-%m-%d')
    until_date = None
    if hasta_fecha.lower() == 'hoy':
        until_date = today_yyyymmdd()
    else:
        until_date = datetime_from_yyyymmdd(until_date)


    base_url = 'http://www.gacetaoficialdebolivia.gob.bo'
        
    url = f'{base_url}/normas/buscarFecha/{from_date}/{until_date}/page:1'
    print(url)

    metadata = []
    archivo_metadata = os.path.join('normas',f'{today_yyyymmdd()}_gaceta_metadata.json')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1284, 'height': 780},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        await random_sleep(2, 9)

        btn_siguiente_el = await get_all_elements_from_locator(page, selectors['lista de normas']['botón siguiente'])

        normas_pagina = []
        pagina = 0
        # Página por página
        while True:
            print(f'------ página: {pagina} -------')
            titulos_el = await get_all_elements_from_locator(page,
                selectors['lista de normas']['título'])
            codigos_el = await get_all_elements_from_locator(page,
                selectors['lista de normas']['código'])
            cabeceras_el = await get_all_elements_from_locator(page,
                selectors['lista de normas']['cabecera meta'])
            enlaces_el = await get_all_elements_from_locator(page,
                selectors['lista de normas']['enlace'])

            # extrayendo datos de cada norma
            for i in range(0, len(titulos_el)):
                print(f'norma. {i}:')
                norma = {}
                norma['nombre'] = (await titulos_el[i].inner_text()).strip()
                norma['nroEnGaceta'] = await codigos_el[i].inner_text()
                cabecera_text = await cabeceras_el[i].inner_text()
                norma['fecha'] = cabecera_text.split('| Fecha de Publicación: ')[1].split(' |')[0]
                fecha = datetime_from_yyyymmdd(norma['fecha'])
                norma['MM/AAAA'] = fecha.strftime('%m/%Y')
                norma['mesAnio'] = f'{mes_from_number(fecha.strftime("%m"))}/{fecha.year}'
                norma['tipoNorma'] = norma['nombre'].split(' N°')[0]
                enlace = await enlaces_el[i].get_attribute('href')
                norma['enlaceNorma'] = f"{base_url}{enlace}"

                # Deberia estar en formato como el ejemplo:
                # "nombre": "Decreto Presidencial N° 5487",
                # "nroEnGaceta": "1965NEC",
                # "fecha": "2025-11-13",
                # "MM/AAAA": "11/2025",
                # "mesAnio": "noviembre/2025",
                # "tipoNorma": "Decreto Presidencial",
                # "enalceNorma": "/normas/verGratis_gob/280965",
                # "enlaceNorma": "http://www.gacetaoficialdebolivia.gob.bo/normas/verGratis_gob/280965"

                print(norma)
                metadata.append(norma)
                
                guardar_progreso(metadata, archivo_metadata)

            btn_siguiente_el = await get_all_elements_from_locator(page,
                selectors['lista de normas']['botón siguiente'])

            if len(btn_siguiente_el) > 0:
                await btn_siguiente_el[0].click()
                # TODO: Cambiar a networkidle o hasta que se cargue la página
                await random_sleep(4,10)
            else:
                break

            pagina += 1

        print(f'Terminado, obtenidos en total: {len(metadata)}. Páginas: {pagina}')


async def obtener_normas_desde_metadata(archivo=None):
    """Obtiene las normas desde una lista de metadatos, las convierte en markdown
    y las guarda en el directorio correspondiente.
    Args:
        archivo_metadata (str): Si se provee lee este archivo y obtiene las normas en este.
        Si no se provee, busca en normas/ el último archivo que termine en _gaceta_metadata.json
    y obtiene las normas sólo de este.
    """

    archivo_metadata = None
    if archivo is not None:
        archivo_metadata = Path(archivo)
    else:
        archivo_metadata = obtener_archivo_metadata_mas_reciente()

    print(f"Obteniendo normas desde archivo {archivo_metadata}")
        
    with open(archivo_metadata, 'r', encoding='utf-8') as f:
        normas = json.load(f)

    for norma in normas:
        url = norma['enlaceNorma']
        anio = norma['MM/AAAA'].split('/')[-1]
        nombre_base = limpiar_nombre(norma['nombre'])
       
        # Buscar carpeta, sino existe crearla
        ruta_carpeta = os.path.join("normas", "raw", anio)
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        ruta_archivo = os.path.join(ruta_carpeta, f"{nombre_base}.md")

        # Saltar si ya existe (útil si el proceso se interrumpe)
        if os.path.exists(ruta_archivo):
            print(f'Ya existe {ruta_archivo}')
            continue
        
        # Navegar y obtener contenido
        try:
            print(f"Ingresando a {url}")
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            seccion_norma = soup.select_one('#seleccion')

            if seccion_norma:
                # convirtiendo a markdown
                contenido_md = md(str(seccion_norma), heading_style="ATX")

                # guardando archivo
                with open(ruta_archivo, 'w', encoding='utf-8') as f_md:
                    f_md.write(contenido_md)

                print(f'Guardado: {ruta_archivo}')
            else:
                print(f"No se encontró el ID en: {url}")

            pausa = random.randint(1, 2)
            print(f'Pausa {pausa} segundos...')
            time.sleep(pausa)
            
        except Exception as e:
            print(f"Error procesando {url}: {e}")


async def unificar_metadatos():
    """Lee todos los archivos de metadatos y archivos descargados para crear un nuevo archivo
    de metadatos unificado y completo.
    """
    ruta_dir = Path('normas/')
    if not ruta_dir.is_dir():
        print(f"El directorio no existe.")
        return None

    # Patrón para validar y extraer la fecha del nombre

    archivos_validos = []
    for archivo in ruta_dir.glob("*metadata.json"):
        archivos_validos.append(archivo)

    if not archivos_validos:
        print("No se encontraron archivos con el formato esperado.")
        return None

    normas = []
    for archivo in archivos_validos:
        with open(archivo, 'r', encoding='utf-8') as f:
            _normas = json.load(f)
            normas.extend(_normas)

    abrogadas = []
    with open(ARCHIVO_ABROGADAS, 'r', encoding='utf-8') as f:
        abrogadas = json.load(f)

    nueva_metadata = []
    normas_guardadas = []
    procesados = 0
    for i, norma in enumerate(normas):
        url = norma['enlaceNorma']
        anio = norma['MM/AAAA'].split('/')[-1]        
        nombre_base = limpiar_nombre(norma['nombre'])

        # Buscar carpeta, sino existe crearla
        ruta_carpeta = os.path.join("normas", "raw", anio)
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        ruta_archivo = os.path.join(ruta_carpeta, f"{nombre_base}.md")            
        
        contenido_md = ''
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f_md:
                contenido_md = f_md.read()
        except Exception as e:
            print(f"Error leyendo {ruta_archivo}: {e}")

        # determinando fuente del archivo (desde su nombre)
        fuente = FUENTE_GACETA
        if ruta_archivo.find("---") != -1:
            fuente = FUENTE_LEXIVOX

        nombre = obtener_nombre_desde_contenido(contenido_md, fuente)
        
        es_abrogada = next((item for item in abrogadas if item['nombre'] == nombre), False)

        metadata = {
            'enlaceNorma': url,
            'MM/AAAA': norma['MM/AAAA'],
            'nombre': nombre,
            'mesAnio': norma['mesAnio'],
            'fecha': norma['mesAnio'],
            'tipoNorma': norma['tipoNorma'],
            #'archivoNorma': ruta_archivo.replace("°", "").replace("º", ""),
            'archivoNorma': ruta_archivo,
            'fuente': fuente,
            'nroEnGaceta': norma.get('nroEnGaceta', '').strip(),
            'estado': 'no vigente' if es_abrogada else 'vigente'
        }

        # verificando duplicados
        if next((item for item in normas_guardadas if item[0] == nombre), None) is not None and \
           next((item for item in normas_guardadas if item[1] == metadata['MM/AAAA']), None) is not None:
            encontrado = next((item for item in nueva_metadata if item['nombre'] == nombre), None)
            print(f'*** Ya existe {nombre} {metadata["MM/AAAA"]}\n{metadata}\nEncontrado:\n{encontrado}')
            continue
        
        nueva_metadata.append(metadata)
        normas_guardadas.append((nombre, metadata['MM/AAAA']))
        procesados += 1
        if i%100 == 0:
            print(f'Procesados {procesados}. Totales: {i}. Ùltimo:\n{metadata}')
    

    # Open file and write the list as JSON
    with open("normas/metadatos.json", "w", encoding="utf-8") as file:
        json.dump(nueva_metadata, file, indent=2, ensure_ascii=False)
        print(f'Escritos {len(nueva_metadata)} registros. Totales encontrados: {procesados}')
