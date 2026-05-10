# Compilación de normativa Boliviana

Proyecto de experimentación, desde leyes hasta reglamentaciones.

Datos obtenidos de:

- [lexivox.org](https://www.lexivox.org) (la mayor parte de la normativa)

Licencia GPL v3 para el software.

Requisitos:

`pip install beautifulsoup4 markdownify lxml playwright asyncclick asyncio click`

## Datos

Guardados en formato markdown en [normas/](normas/)

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

## Visor

Construido con node.js para generar un sitio estático con búsqueda de flexsearch.


Construir
```
cd src/visor
npm install
node build.js
```

Resultados en ouput

Correr servidor de prueba
```
npx serve output
```
