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
from playwright.async_api import async_playwright
from src.scraper.common.selectors import get_selector_value, get_locator, get_all_elements_from_locator
from src.common.custom_logger import CustomLogger
from src.common.time import random_sleep, today_yyyymmdd, age_in_days, datetime_from_yyyymmdd, mes_from_number


LOGGER = CustomLogger('gaceta - metadata ')

selectors = {
    "lista de normas": {
        "título": {
            "value": "//div[@class='row']//h6",
            "type": "xpath"
        },
        'código': {
            "value": "//div[@class='row']//div[@class='card-body']//p[contains(text(), 'Publicado en')]/strong/a",
            "type": "xpath"
        },
        "cabecera meta": {
            "value": "//div[@class='row']//div[@class='card-body']//p[contains(text(), 'Publicado en')]",
            # para obtener la fecha de publicación hay que filtrar el texto entre '| Fecha de Publicación: <fecha> |'
            #  | Fecha de Publicación: 2025-11-09 |  Formato de fecha YYYY-MM-DD
            "type": "xpath"
        },
        "enlace": {
            "value": "//div[@class='row']//div[@class='card-footer bg-transparent text-end']/a[text()='Ver Norma']",
            "type": "xpath"
        },
        "botón siguiente": {
            "value": "//div[@class='paging']/a[not(@class='disabled')][text()='siguiente >>']",
            "type": "xpath"
        }
    }
}


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
 

async def obtener_metadata(desde_fecha, hasta_fecha):
    from_date = datetime_from_yyyymmdd(desde_fecha).strftime('%Y-%m-%d')
    until_date = None
    if hasta_fecha.lower() == 'hoy':
        until_date = today_yyyymmdd()
    else:
        until_date = datetime_from_yyyymmdd(until_date)

    url = f'http://www.gacetaoficialdebolivia.gob.bo/normas/buscarFecha/{from_date}/{until_date}/page:1'
    print(url)

    metadata = []
    archivo_metadata = os.path.join('..','..','..','normas',f'{today_yyyymmdd()}_gaceta_metadata.json')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1284, 'height': 780},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        await random_sleep(5, 12)

        btn_siguiente_el = await get_all_elements_from_locator(selectors['lista de normas']['botón siguiente'])

        normas_pagina = []
        # Página por página
        while True:
            titulos_el = await get_all_elements_from_locator(
                selectors['lista de normas']['título'])
            codigos_el = await get_all_elements_from_locator(
                selectors['lista de normas']['código'])
            cabeceras_el = await get_all_elements_from_locator(
                selectors['lista de normas']['cabecera meta'])
            enalces_el = await get_all_elements_from_locator(
                selectors['lista de normas']['enlace'])

            # extrayendo datos de cada norma
            for i, titulo_el in enumerate(titulos_el):
                print(f'----- pág. {i} -----')
                norma = {}
                norma['nombre'] = titulo_el.inner_text()
                norma['nroEnGaceta'] = codigos_el[i].inner_text()
                cabecera_text = cabeceras_el[i].inner_text()
                norma['fecha'] = cabecera_text.split('| Fecha de Publicación: ').split(' |')[0]
                fecha = datetime_from_yyyymmdd(norma['fecha'])
                norma['MM/AAAA'] = fecha.strftime('%m/%Y')
                norma['mesAnio'] = f'{mes_from_number(fecha.strftime("%m"))}/{fecha.year}'
                norma['tipoNorma'] = norma['nombre'].split(' N°')[0]
                norma['enalceNorma'] = enlaces_el[i].get_attribute('href')
                # {
                #     "enlaceNorma": "https://www.lexivox.org/norms/BO-L-N1690.xhtml",
                #     "nroEnGaceta": " 1963nec",
                #     "tipoNorma": "Ley",
                #     "mesAnio": "noviembre/2025",
                #     "MM/AAAA": "11/2025",
                #     "nombre": "Ley - 1690"
                # },

                print(norma)
                metadata.append(norma)
                
                guardar_progreso(metadatos, archivo_metadata)

            btn_siguiente_el = await get_all_elements_from_locator(
                selector['lista de normasl']['botón siguiente'])

            if len(btn_siguiente_el) > 0:
                await btn_siguiente_el.click()
            else:
                break

        print(f'Terminado, obtenidos en total: {len(metadata)}')


        
