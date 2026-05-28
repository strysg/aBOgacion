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
const { cleanAllHtmlsAndJson, findMetadataFiles } = require('./utils.js');

// ----- CLI argument parsing -----
const args = process.argv.slice(2);
let action = null; // e.g., 'all', 'skip-clean', etc.

for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
        case '--help':
            console.log(`
Usage: node build.js

Options:
  --help        Muestra esta ayuda. Sin opciones construye todas las normas usando el archivo
                /normas/metadatos.json y los archivos markdown /normas/normalized/* para
                crear archivos html. Se sobre entiende previamente se han descargado todos
                los archivos de normativas, construido los metadatos y las normativas en
                markdown han sido normalizadas.
            `);
            process.exit(0);
        default:
            console.warn(`Unknown argument: ${args[i]}`);
    }
}

// ------ Configuration --------
const INPUT_DIR = '../../normas/normalized';
const OUTPUT_DIR = './output';
const SITE_TITLE = 'Visor de normas Bolivianas';

const METADATA_FILE = '../../normas/metadatos.json';

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

    const allMetadata = JSON.parse(await fs.readFile(METADATA_FILE), 'utf-8');

    let count = 0;
    let skipped = 0;
    let skippedList = [];
    let allDocs = [];
    const years = {};
    for (const metadata of allMetadata) {
        // en el archivo de metadata se tiene tambien la ruta del archivo en "archivoNorma", ejemplo: "normas/raw/2020/ley---1344.md",
        // con esto se re escribe como "../../normas/normalized/2020/ley---1344.md"
        const fullPath = path.join(INPUT_DIR, metadata.archivoNorma.split('/').at(-2), metadata.archivoNorma.split('/').at(-1));
        let markdown;
        try {
            markdown = await fs.readFile(fullPath, 'utf-8');
        } catch (err) {
            console.warn(`⚠️ no se ha encontrado el archivo ${fullPath}. Saltando`);
            console.warn(err);
            continue;
        }
        let htmlContent;
        try {
            htmlContent = await marked.parse(markdown);            
        } catch (err) {
            console.error(`❌ Error al parsear ${fullPath}: ${err.message}`);
            skipped++;
            skippedList.push(fullPath);
            htmlContent = `<div class="error">⚠️ No se pudo procesar este documento. <br><small>${err.message}</small></div>
                           <pre>${markdown.slice(0, 1000)}</pre>`;
        }

        // 290 primeros caracteres sin espacios en blanco adicionales
        const textPreview = markdown.replace(/[#*`>\[\]()]/g, '').slice(0, 290).replace(/\s+/g, ' ').
              replace(/\-+/, '').trim();

        // generar Html
        const year = metadata['MM/AAAA'].split('/')[1];
        const yearPath = path.join(OUTPUT_DIR, year);
        if (!fs.existsSync(yearPath)) {
            fs.mkdirSync(yearPath, { recursive: true });
        }
        const cleanName = metadata['nombre'].replaceAll('---', ' ').trim();

        const outputHtmlPath = path.join(yearPath, `${metadata.nombre}.html`);
        const fullHtlm = ejs.render(normasTemplate, {
            id: count,
            ...metadata,
            year,
            siteTitle: SITE_TITLE,
            htmlContent
        });

        try {
            await fs.writeFile(outputHtmlPath, fullHtlm);
        } catch (error) {
            console.warn(`⚠️ No se pudo guardar el documento ${outputHtmlPath}`);
            console.warn(error);
        }
        
        allDocs.push({
            id: count,
            title: cleanName,
            type: metadata.tipoNorma,
            year,
            estado: metadata.estado,
            p: textPreview,
            url: `${year}/${cleanName}.html`
        });
        count++;
        if (count%500 == 0) console.log(`📄 Procesados ${count} archivos (omitidos: ${skipped})...`);

        if (!years[year]) years[year] = 0;
        years[year] += 1;
    }

    // guardando la metadata para ser consumido en el navegador
    await fs.writeFile(path.join(OUTPUT_DIR, 'assets', 'docs.json'), JSON.stringify(allDocs));
    console.log(`✅ Procesamiento completado. ${skipped} archivos omitidos.`);
    skippedList.forEach(omitido => { console.log(`Omitido: ${omitido}`); });

    // TODO: incluir indice por años y otros datos generales en página principal
    const mainHtml = ejs.render(mainTemplate, { title: SITE_TITLE, years });
    await fs.writeFile(path.join(OUTPUT_DIR, 'index.html'), mainHtml);

    console.log('🎉 Build completo. El sitio está en ./output');
}

build().catch(console.error);
