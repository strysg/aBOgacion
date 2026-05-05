"""
Abogacion. (C) Rodrigo Garcia 2026
"""

import asyncclick as click
from src.scraper.gaceta_oficial.obtener import obtener_metadata, obtener_normas_desde_metadata


@click.command()
@click.option("--desde", "-d", default="2025-11-09",
              help="Para obtener las normas desde esta fecha, formato AAAA-MM-DD. Ej. 2025-11-09")
@click.option("--hasta", "-h", default="hoy",
              help="Para obtener las normas hasta esta fecha, formato AAAA-MM-DD. Ej. hoy o 2026-11-11")
@click.option('--solo-normas', "-s", is_flag=True, default=False,
              help="Para obtener las normas asumiendo que el archivo de metadata ya se ha obtenido")

async def get_normas(desde, hasta, solo_normas):
    if solo_normas is False:
        await obtener_metadata(desde, hasta)

    await obtener_normas_desde_metadata()


if __name__ == '__main__':

    get_normas(_anyio_backend='asyncio')
