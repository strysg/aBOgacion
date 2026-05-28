/**
   This is part of aBOgacion
   Copyright Rodrigo Garcia 2026
 */

const fs = require('fs-extra');
const path = require('path');
const ejs = require('ejs');
const { glob } = require('glob');

// Configuration
const INPUT_DIR = '../../normas/normalized';
const OUTPUT_DIR = './output';
const SITE_TITLE = 'Visor de normas Bolivianas';

const METADATA_FILE = '../../normas/metadatos.json';

const LEXIVOX_SEPARATOR = '---';
const GACETA_SEPARATOR = '-n°-';

const FUENTE_LEXIVOX = 'lexivox.org';
const FUENTE_GACETA = 'gaceta oficial';

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
        metadata['fuente'] = FUENTE_LEXIVOX;
    } else if (fileName.indexOf(GACETA_SEPARATOR) !== -1) {
        metadata = parseGacetaFile(fileName);
        metadata['fuente'] = FUENTE_GACETA;
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
    //const jsonFiles = await glob('**/*.json', { cwd: OUTPUT_DIR, absolute: true });
    const jsonFiles = [];
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
 * Recursively finds all files ending with "metadata.json" inside a directory.
 * @param {string} baseDir - The directory to scan (default: '../../normas').
 * @returns {Promise<string[]>} - Array of absolute file paths.
 */
async function findMetadataFiles(baseDir = '../../normas') {
    const pattern = path.join(baseDir, '**', '*metadata.json');
    const files = await glob(pattern, { absolute: false });
    console.log(`🔍 Encontrados ${files.length} archivos metadata.json en ${baseDir}`);
    return files;
}

/**
 * Dado el contenido de una normativa, busca el nombre en los titulares de este.
 * La búsqueda varía según la fuente pues el formato de cada una es diferente.
 * @param {string} contenido - Cadena en markdown
 * @param {string} fuente - Fuente desde donde se extrajo el contenido
 * @returns {string}
 */
function obtenerNombreDesdeContenido(contenido, fuente) {
   // Dividir el contenido en líneas
    const lines = contenido.split(/\r?\n/);
    let normName = '';
    if (fuente === FUENTE_GACETA) {
        /*
         **TEXTO DE CONSULTA**    
         Gaceta Oficial del Estado Plurinacional de Bolivia   
         Derechos Reservados © 2026

         ---

         **DECRETO PRESIDENCIAL N° 5522**  
         **RODRIGO PAZ PEREIRA**  
         **PRESIDENTE CONSTITUCIONAL DEL ESTADO PLURINACIONAL DE BOLIVIA**           

         Retorna: decreto-presidencial-5522
        */
        
        // Encontrar el índice del separador "---"
        let separatorIndex = -1;
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim() === "---") {
                separatorIndex = i;
                break;
            }
        }
        
        if (separatorIndex === -1) return "";
        
        // Patrón para identificar "TIPO N° NÚMERO" (con N° o Nº)
        const pattern = /^([A-Z\s]+N[°º]\s*\d+)/;
        
        // Recorrer las líneas después del separador
        for (let i = separatorIndex + 1; i < lines.length; i++) {
            // Eliminar marcadores de negrita (**) y espacios
            let cleaned = lines[i].replace(/\*\*/g, '').trim();
            if (!cleaned) continue;
            
            const match = cleaned.match(pattern);
            if (match) {
                normName = match[1];
                // Normalizar: minúsculas y espacios por guiones
                normName = normName.toLowerCase().replace(/\s+/g, '-').trim();
                break;
            }
        }
    }
    if (fuente === FUENTE_LEXIVOX) {
        /*
          Ejemplo:
          # Bolivia: Decreto Supremo Nº 29760, 24 de octubre de 2008

          Retorna: decreto-supremo-29760
        */
        let lineNumber = 0;
        // hasta las 50 primeras lineas buscando el titular
        for (let i = 0; i < 50; i++) {
            if (lines[i].indexOf('# Bolivia:') !== -1) {
                lineNumber = i;
                break;
            }
        }

        normName = lines[lineNumber].split("# Bolivia: ")[1].trim();
        if (normName.split(',').length > 1) {
            normName = normName.split(',')[0].trim();
        }

    }
    // limpiando espacios en blanco adicionales o guiones
    normName = normName.toLowerCase().replace(/n[°º]/g, ' ');
    normName = normName.replace(/\s/g, '-');
    normName = normName.replace(/-{2,}/g, '-');
    return normName.trim();
}

module.exports = {
    parseLexivoxFile,
    parseGacetaFile,
    parseFile,
    cleanAllHtmlsAndJson,
    scanMarkdownFiles,
    findMetadataFiles,
};

