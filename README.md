# Compilación de normativa Boliviana

Proyecto de experimentación, desde leyes hasta reglamentaciones.

Datos obtenidos de:

- [lexivox.org](https://www.lexivox.org) (la mayor parte de la normativa)
- [http://www.gacetaoficialdebolivia.gob.bo/](http://www.gacetaoficialdebolivia.gob.bo/) (las últimas normas)

Licencia GPL v3 para el software.

Requisitos:

`pip install beautifulsoup4 markdownify lxml playwright asyncclick asyncio click`

## Datos

Los datos ya están listos y guardados en formato markdown en [normas/](normas/)

```
normas
├── 1945
│   ├── ley---19451231-1.md
│   └── ley---19451231-6.md
├── 1946
│   └── ley---19460102.md
...
├── 2025
│   ├── resolución-suprema---31901.md
│   ├── resolución-suprema---31902.md
│   └── resolución-suprema---31903.md
...
```

### Obtención de datos (desde cero)

> No es necesario que hagas este paso a menos que necesites experimentar y volver a descargar todo nuevamente (toma mucho tiempo)

```
# Activar entorno virtual, luego:
# lexivox
cd src/scraper/lexivox
python obtener_metadata.py
python obtener_normas.py

# gaceta
cd <ruta raiz del proyecto>
python obtener_gaceta.py
```

Todo se guardará en `normas/raw`

### Normalizar archivos markdown

Se debería ejecutar el notebook jupyter: [src/data-handlers/normalize.ipynb](src/data-handlers/normalize.ipynb). Va a guardar las normativas en `normas/normalized`

## Visor

Construido con node.js para generar un sitio estático con búsqueda de flexsearch.

Construir
```
cd src/visor
npm install
node build.js
# node build.js -f para hacer reconstrucción rápida en caso de haber echo build.js completo antes)
```

Resultados en ouput

Correr servidor de prueba
```
npx serve output
```
