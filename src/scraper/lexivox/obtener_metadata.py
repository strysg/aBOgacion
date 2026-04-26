"""
Abogashon. (C) Rodrigo Garcia 2026
"""

import os
import requests
import random
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
from lxml import etree


selectors = {
    'norma': {
        'título de norma': {
            'value': '//a[@id="norm"]/../../h1',
            'type': 'xpath'
        },
    },
    'lista de normas': {
        'boton siguiente': {
            'value': '//a[@title="Siguiente"]',
            'type': 'xpath'
        },
        'entrada de norma': {
            'value': '//ol//li',
            'type':'xpath'
        },
        'enlace a norma': {
            'value': '//h3/following-sibling::a[contains(@onclick,"verNorma")]',
            'type': 'xpath'
        },
        'tipo de norma abrev.': {
            'value': '//ol/li/i',
            'type': 'xpath'
        },
        'nro en gaceta': {
            'value': '//ol/li//p/a[@class="tag"][contains(text(),"Gaceta")]',
            'type': 'xpath'
        },
        'titulo abrev': {
            'value': '//ol/li//span[@title="Número"]',
            'type': 'xpath',
        },
        'chips de normas': {
            'value': '//ol//li//p/a[@class="tag"]',
            # para el tipo de norma seria [2+(n*3)] donde n seria el numero de norma mostrado
            # para el mes y anio seria [3+(n*3)] donde n seria el numero de norma mostrado
            # para el numero en gaceta seria [n*3] donde n seria el numero de norma mostrado
            'type':'xpath'
        },
        'tipo de norma': {
            'value': '(//ol/li//p/a[@class="tag"])[2]',
            'type': 'xpath'
        },
        'mes y año': {
            'value': '(//ol/li//p/a[@class="tag"])[3]',
            'type': 'xpath'
        }
    }
}

# --------- utils ------------
def soup_de_url(url, headers):
    print(f'Obteniendo página de {url}')
    respuesta = requests.get(url, headers=headers)

    if respuesta.status_code == 200:
        soup = BeautifulSoup(respuesta.content, 'html.parser')
        print("Soup descargado correctamente.")
        return soup
    else:
        print(f"Error al descargar: {respuesta.status_code}")


def obtener_mes_anio(_str):
    meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05',
            'junio': '06', 'julio': '07', 'agosto':'08', 'septiembre': '09',
            'octubre': '10', 'noviembre':'11', 'diciembre':'12'}
    mes = meses[_str.split('/')[0].lower()]
    return f'{mes}/{_str.split("/")[1]}'


def metadatos_normas(dom):
    metadatos = []
    _selectors = selectors['lista de normas']
    _entradas = dom.xpath(_selectors['entrada de norma']['value'])
    for i, _entrada in enumerate(_entradas):
        metadata = {}
        _el = _entrada.xpath('.//h3/following-sibling::a[contains(@onclick,"verNorma")]')
        if not _el:
            print('xx No se encontró norma ')
            return metadata
        metadata['enlaceNorma'] = _el[0].get('href')
        chips = _entrada.xpath('.//p/a[@class="tag"]')
        for chip in chips:
            if chip.text.lower().startswith('gaceta'):
                metadata['nroEnGaceta'] = chip.text.lower().split('gaceta')[1]
            elif len(chip.text.lower().split('/')) > 1:
                metadata['mesAnio'] = chip.text
                metadata['MM/AAAA'] = obtener_mes_anio(metadata['mesAnio'])
            else:
                metadata['tipoNorma'] = chip.text

        _el = _entrada.xpath('.//span[@title="Número"]')
        if _el:
            metadata['nombre'] = f'{metadata.get("tipoNorma", "")} - {_el[0].text}'

        metadatos.append(metadata)
    print(f'obtenidos: {len(metadatos)}')

    return metadatos


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


# ----------------- main --------------

fecha_hoy = datetime.now().strftime('%d-%m-%Y')[
archivo_metadata = os.path.join('..','..','..','normas',f'{fecha_hoy}_metadata.json')
metadatos = []

# pagina 1
url = "https://www.lexivox.org/packages/lexml/buscar_normas.php?id_tipo_norma=&nro_norma=&search_xml=&id_pais=25&estado=vigentes&con_jurisprudencia=f&dcmi_identifier=&fecha_promulgacion_min=1825-08-08&fecha_promulgacion_max=2026-11-09&defaultGroupValue=1" 
headers = {'User-Agent': 'Bot severios (rgarcia@laotra.red)'}
soup = soup_de_url(url, headers)

# de cada página se extraen las urls y metadatos de cada norma
normas = []

existe_siguiente = True
nro_pagina = 0

while existe_siguiente:
    print(f'----- Nro página {nro_pagina} ------')
    dom = etree.HTML(str(soup))
    metadatos = metadatos_normas(dom)
    normas.append(metadatos)
    _els = dom.xpath(selectors['lista de normas']['boton siguiente']['value'])
    if not _els:
        existe_siguiente = False
        continue

    guardar_progreso(metadatos, archivo_metadata)
    
    pausa = random.randint(2, 8)
    print(f'Pausa {pausa} segundos...')
    time.sleep(pausa)

    url = f'https://www.lexivox.org/{_els[0].get('href').split('../../')[1]}'
    soup = soup_de_url(url, headers)
    nro_pagina += 1

print(f'======> Obtenidos: {len(metadatos)}')
