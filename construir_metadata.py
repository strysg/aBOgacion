"""
Abogacion. (C) Rodrigo Garcia 2026
"""

import asyncclick as click
from src.scraper.gaceta_oficial.obtener import unificar_metadatos


@click.command()
async def unificar():
    await unificar_metadatos()


if __name__ == '__main__':
    unificar(_anyio_backend='asyncio')
