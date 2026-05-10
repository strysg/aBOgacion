/**
   This is part of aBOgacion
   Copyright Rodrigo Garcia 2026
 */

const fs = require('fs-extra');
const path = require('path');
const ejs = require('ejs');
const { glob } = require('glob');

// Configuration
const INPUT_DIR = '../../normas';
const OUTPUT_DIR = './output';
const SITE_TITLE = 'Visor de normas Bolivianas';

const LEXIVOX_SEPARATOR = '---';
const GACETA_SEPARATOR = '-n°-';

/**
 * Obtiene metadatos de un archivo descargado desde lexivox
 * @param filename (string) - Nombre del archivo
 * @returns Object with {title, normType, filename }
 */
function parseLexivoxFile(filename) {

    const parsed = {};
    parsed.filename = filename;
    // ejemplo: ley---1690.md
    parsed.normType = filename.split(LEXIVOX_SEPARATOR)[0]; // ley
    // ejemplo: ley 1690
    parsed.title = filename.replace(/\.md$/, '')
        .replace(new RegExp(`^[a-z\-]+${LEXIVOX_SEPARATOR}`), '');
    // mejorar en caso de ser solo un número
    if (/^\d+$/.test(parsed.title)) parsed.title = `${parsed.normType} ${parsed.title}`;
    return parsed;
}

/**
 * Obtiene metadatos de un archivo descargado desde la gaceta
 * @param filename (string) - Nombre del archivo
 * @returns Object with {title, normType, filename }
 */
function parseGacetaFile(filename) {
    const parsed = {};
    parsed.filename = filename;
    parsed.normType = filename.split(GACETA_SEPARATOR)[0]; // ley
    parsed.title = filename.replace(/\.md$/, '')
        .replace(new RegExp(`^[a-z\-]+${GACETA_SEPARATOR}`), '');
    // mejorar en caso de ser solo un número
    if (/^\d+$/.test(parsed.title)) parsed.title = `${parsed.normType} ${parsed.title}`;
    return parsed;
} 

function parseFile(filePath) {
    const parts = filePath.split(path.sep);
    const year = parts[parts.length-2];                     // e.g. "1945"
    const fileName = parts[parts.length-1];                 // e.g. "ley---19451231-1.md"
    
    let metadata;
    if (fileName.indexOf(LEXIVOX_SEPARATOR) !== -1) {
        metadata = parseLexivoxFile(fileName);
        metadata['fuente'] = 'lexivox.org';
    } else if (fileName.indexOf(GACETA_SEPARATOR) !== -1) {
        metadata = parseGacetaFile(fileName);
        metadata['fuente'] = 'gaceta oficial de Bolivia';
    } else {
        // FALLBACK for unknown formats
        metadata = {
            filename: fileName,
            normType: 'Documento misceláneos',
            title: fileName.replace(/\.md$/, ''),
            fuente: 'indeterminado'
        };
    }
    metadata.year = year;
    return metadata;
}

async function cleanAllHtmlsAndJson() {
    console.log(`🧹 Limpiando archivos .html y .json previos en ${OUTPUT_DIR}...`);
    await fs.ensureDir(OUTPUT_DIR);

    // Find all .html and .json files recursively inside OUTPUT_DIR
    const htmlFiles = await glob('**/*.html', { cwd: OUTPUT_DIR, absolute: true });
    const jsonFiles = await glob('**/*.json', { cwd: OUTPUT_DIR, absolute: true });
    const allFiles = [...htmlFiles, ...jsonFiles];

    let deletedCount = 0;
    for (const file of allFiles) {
        try {
            await fs.unlink(file);
            deletedCount++;
        } catch (err) {
            console.warn(`No se pudo borrar ${file}: ${err.message}`);
        }
    }

    console.log(`✅ Eliminados ${deletedCount} archivos .html y .json.`);
}

/**
 * Scans all markdown files in the INPUT folder
 * @returns list of files of type glob
*/
async function scanMarkdownFiles() {
  const files = await glob(`**/*.md`, { cwd: INPUT_DIR, absolute: false });
  console.log(`✅ Encontrados ${files.length} archivos .md en ${INPUT_DIR}.`);
  return files;
}

function escapeHtml(str) {
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

/**
 * Escanea las normas en la carpeta normas/ y dados los archivos de metadata,
 * construye un nuevo conjunto de metadatos con información adicional para ser
 * leída y generar contenido en HTML por cada norma y que esta sea indexable
 * @param metadataFiles (array[string]) - Array de rutas con los archivos de metadata a tomar en cuenta
 * @returns array[obj] - Array de metadata con objetos con el siguiente formato de ejemplo:
 * {
        "nombre": "Decreto Presidencial N° 5486",
        "nroEnGaceta": "1964NEC",
        "fecha": "2025-11-09",     -- puede ser ""
        "MM/AAAA": "11/2025",
        "mesAnio": "noviembre/2025",
        "tipoNorma": "Decreto Presidencial",
        "enlaceNorma": "http://www.gacetaoficialdebolivia.gob.bo/normas/verGratis_gob/280962",
        "archivoNorma": "normas/2025/decreto-presidencial---5486.md,
        "fuente": "gaceta oficial de Bolivia"
 * }
 *
 */
async function loadMarkdownFilesFromMetadata (metadataFiles = []) {
    const newMetadata = [];

    // Load all metadata JSON files into an array of objects
    let allMetadataRecords = [];
    for (const metadataFile of metadataFiles) {
        const content = await fs.readFile(path.join(__dirname, metadataFile), 'utf-8');
        const records = JSON.parse(content);
        allMetadataRecords.push(...records);
    }

    // Get all markdown files from the input directory
    const mdFiles = await scanMarkdownFiles();

    let count = 0;
    let fallidosCount = 0;
    for (const mdFilepath of mdFiles) {
        const fullPath = path.join(INPUT_DIR, mdFilepath);
        const metadata = parseFile(fullPath); // returns { title, normType, year, filename, fuente? }

        let match = null;
        for (const record of allMetadataRecords) { 
            const titleMatch = record.nombre.split(' ').at(-1) === metadata.title.split(' ').at(-1);
            const typeYearMatch = record.tipoNorma.toLowerCase() === metadata.normType.replaceAll('-', ' ').toLowerCase() &&
                  record['MM/AAAA'].split('/')[1] === metadata.year;
            if (titleMatch || typeYearMatch) {
                match = record;
                break;
            }
        }

        if (match) {
            newMetadata.push({
                nombre: metadata.title,
                tipoNorma: metadata.normType,
                year: metadata.year,
                fecha: match.fecha || '',
                mesAnio: match.mesAnio || '',
                enlaceNorma: match.enlaceNorma || '',
                archivoNorma: mdFilepath,
                nroEnGaceta: match.nroEnGaceta || '',
                'MM/AAAA': match['MM/AAAA'] || '',
                fuente: match.fuente || metadata.fuente || 'desconocido'
            });
        } else {
            console.log(`No se encontró metadata para: ${mdFilepath}`);
	    console.log(metadata);
            // Optionally still include with minimal info
            newMetadata.push({
                nombre: metadata.title,
                tipoNorma: metadata.normType,
                year: metadata.year,
                fecha: '',
                archivoNorma: mdFilepath,
                nroEnGaceta: '',
                mesAnio: '',
                enlaceNorma: '',
                fuente: metadata.fuente || 'gaceta oficial'
            });
            fallidosCount++;
        }
        if (++count %200 === 0) console.log(`Procesados archivos ${count}, no encontrados: ${fallidosCount}`);
    }
    return newMetadata;
}

module.exports = {
    parseLexivoxFile,
    parseGacetaFile,
    parseFile,
    cleanAllHtmlsAndJson,
    scanMarkdownFiles,
    loadMarkdownFilesFromMetadata
};

