/**
   This is part of aBOgacion
   Copyright Rodrigo Garcia 2026
 */

const fs = require('fs-extra');
const path = require('path');
const ejs = require('ejs');
const { marked } = require('marked');
const FlexSearch = require('flexsearch');
const { glob } = require('glob');
const { cleanAllHtmlsAndJson, findMetadataFiles, loadMarkdownFilesFromMetadata } = require('./utils.js');

// ----- CLI argument parsing -----
const args = process.argv.slice(2);
let action = null; // e.g., 'all', 'skip-clean', etc.

for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
        case '-f':
            action = 'fast';
            break;
        case '--help':
            console.log(`
Usage: node build.js [options]

Options:
  -f <action>   Para construir sin volver a generar el archivo output/metadata.json.
                Sin esta opción
                se vuelve a buscar todos los archivos markdown en /normas/ y se los intentan encontrar 
                en los archivos de metada (/normas/*.metadata.json para asegurar se actualice todo.
                Possible actions: "force" (delete everything), "append" (keep existing, only add new)
  --help        Show this help message
            `);
            process.exit(0);
        default:
            console.warn(`Unknown argument: ${args[i]}`);
    }
}

// Example: if action === 'force', we will use the aggressive cleaner
const FAST_BUILD = (action === 'fast');

// ------ Configuration --------
const INPUT_DIR = '../../normas';
const OUTPUT_DIR = './output';
const SITE_TITLE = 'Visor de normas Bolivianas';

const LEXIVOX_SEPARATOR = '---';
const GACETA_SEPARATOR = '-n°-';

// Search index (FlexSearch)
const index = new FlexSearch.Document({
  document: {
    id: 'id',
    index: ['title', 'type', 'year', 'content_preview'],
    store: ['title', 'type', 'year', 'url']
  }
});


// -------------------------------------
async function build() {
    console.log('⚒️ Construcción de sitio estático para visor de normas bolivianas.');

    await cleanAllHtmlsAndJson();
    await fs.ensureDir(path.join(OUTPUT_DIR, 'assets'));

    // cargar plantillas ejs
    const normasTemplate = await fs.readFile(path.join(__dirname, 'templateNorma.ejs'), 'utf-8');
    const mainTemplate = await fs.readFile(path.join(__dirname, 'templateMain.ejs'), 'utf-8');

    let files = [];
    if (FAST_BUILD) {
        console.log('⏩ Construcción rápida (evitando actualización de metadata)');
        files = JSON.parse(await fs.readFile(path.join(OUTPUT_DIR, 'metadata.json'), 'utf-8'));
    } else {
        console.log('🔨 Iniciando construcción completa (actualizando metadata)');
        const metadataFiles = await findMetadataFiles();
        files = await loadMarkdownFilesFromMetadata(metadataFiles);
        // guardando la metadata cargado de documentos json y archivos markdown
        // util cuando se quiere evitar la función loadmarkdownfilesfrommetadata
        await fs.writeFile(path.join(OUTPUT_DIR, 'metadata.json'), JSON.stringify(files));
    }


    let count = 0;
    let skipped = 0;
    let skippedList = [];
    let allDocs = [];

    const years = {};
    
    for (const fileMetadata of files) {
        const fullPath = path.join(INPUT_DIR, fileMetadata.archivoNorma);

        const rawMarkdown = await fs.readFile(fullPath, 'utf-8');
        // markdown a HTML
        let htmlContent;
        try {
            htmlContent = await marked.parse(rawMarkdown);
        } catch (err) {
            console.error(`❌ Error al parsear ${fullPath}: ${err.message}`);
            skipped++;
            skippedList.push(fullPath);
            htmlContent = `<div class="error">⚠️ No se pudo procesar este documento. <br><small>${err.message}</small></div>
                           <pre>${rawMarkdown.slice(0, 1000)}</pre>`;
        }

        const textPreview = rawMarkdown.replace(/[#*`>\[\]()]/g, '').slice(0, 290);

        // generar html
        const yearPath = path.join(OUTPUT_DIR, fileMetadata.year);
        if (!fs.existsSync(yearPath)) {
            fs.mkdirSync(yearPath, { recursive: true });
        }
        const outputHtmlPath = path.join(yearPath, `${fileMetadata['nombre']}.html`);
        const fullhtml = ejs.render(normasTemplate, {
            ...fileMetadata,
            siteTitle: SITE_TITLE,
            htmlContent: htmlContent
            // TODO agregar mas metadatos como la fuente, la url en la gaceta o lexivox
        });

        fs.writeFileSync(outputHtmlPath, fullhtml);
        // console.log(`Archivo ${outputHtmlPath} guardado.`);
        allDocs.push({
            id: count,
            title: fileMetadata.nombre,           // e.g. "Resolución Suprema N° 32206"
            type: fileMetadata.tipoNorma,         // e.g. "Resolución Suprema"
            year: fileMetadata.year,
            p: textPreview,
            url: `${fileMetadata.year}/${fileMetadata.nombre}.html`  // include .html
        });
        count ++;
        if (count % 500 === 0) console.log(`📄 Procesados ${count} archivos (omitidos: ${skipped})...`);

        if (years[fileMetadata['year']] === undefined) {
            years[fileMetadata['year']] = 1;
        } else {
            years[fileMetadata['year']] = years[fileMetadata['year']] + 1;
        }
    }

    // guardando la metadata de todos los documentos
    await fs.writeFile(path.join(OUTPUT_DIR, 'assets', 'docs.json'), JSON.stringify(allDocs));

    console.log(`✅ Procesamiento completado. ${skipped} archivos omitidos.`);
    skippedList.forEach(omitido => { console.log(`Omitido: ${omitido}`); });

    // Constuir la serialización del índice de búsqueda
    // const indexState = index.export();
    // await fs.writeFile(path.join(OUTPUT_DIR, 'assets', 'index.json'), JSON.stringify(indexState));

    //const years = ['2025', '2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012'];


    // TODO: incluir indice por años y otros datos generales en página principal
    const mainHtml = ejs.render(mainTemplate, { title: SITE_TITLE, years });
    await fs.writeFile(path.join(OUTPUT_DIR, 'index.html'), mainHtml);

    console.log('🎉 Build completo. El sitio está en ./output');
}

build().catch(console.error);
