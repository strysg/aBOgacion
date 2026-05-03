"""
Abogacion. (C) Rodrigo Garcia 2026
"""

import asyncclick as click
from src.scraper.gaceta_oficial.obtener import obtener_metadata


@click.command()
@click.option("--desde", "-d", default="2025-11-09",
              help="Para obtener las normas desde esta fecha, formato AAAA-MM-DD. Ej. 2025-11-09")
@click.option("--hasta", "-h", default="hoy",
              help="Para obtener las normas hasta esta fecha, formato AAAA-MM-DD. Ej. hoy o 2026-11-11")
async def get_metadata(desde, hasta):
    await obtener_metadata(desde, hasta)

    


if __name__ == '__main__':

    get_metadata(_anyio_backend='asyncio')
