"""
Abogacion. (C) Rodrigo Garcia 2026
"""
import re
import json

FUENTE_GACETA = "gaceta oficial"
FUENTE_LEXIVOX = "lexivox.org"
ARCHIVO_ABROGADAS = "normas/abrogadas.json"


def obtener_nombre_desde_contenido(contenido: str, fuente: str) -> str:
    """
    Dado el contenido de una normativa y la fuente, extrae el nombre normalizado.
    
    Args:
        contenido (str): Cadena en markdown.
        fuente (str): Fuente del contenido ('gaceta' o 'lexivox').
    
    Returns:
        str: Nombre normalizado, o cadena vacía si no se encuentra.
    """
    lines = contenido.splitlines()
    norm_name = ""
    
    if fuente == FUENTE_GACETA:
        # Buscar el separador "---"
        separator_index = -1
        for i, line in enumerate(lines):
            if line.strip() == "---":
                separator_index = i
                break
        
        if separator_index == -1:
            return ""
        
        # Patrón para "TIPO N° NÚMERO"
        pattern = re.compile(r'^([A-Z\s]+N[°º]\s*\d+)')
        
        # Recorrer líneas después del separador
        for i in range(separator_index + 1, len(lines)):
            # Eliminar marcadores de negrita y espacios
            cleaned = lines[i].replace('**', '').strip()
            if not cleaned:
                continue
            
            match = pattern.match(cleaned)
            if match:
                norm_name = match.group(1)
                # Normalizar: minúsculas y espacios por guiones
                norm_name = norm_name.lower().replace(' ', '-').strip()
                break
    
    elif fuente == FUENTE_LEXIVOX:
        # Buscar "# Bolivia:" en las primeras 50 líneas
        line_number = -1
        for i in range(min(50, len(lines))):
            if "# Bolivia:" in lines[i]:
                line_number = i
                break
        
        if line_number != -1:
            # Extraer después del prefijo
            parts = lines[line_number].split("# Bolivia: ", 1)
            if len(parts) == 2:
                norm_name = parts[1].strip()
                # Si contiene coma, tomar la parte antes de la primera coma
                if ',' in norm_name:
                    norm_name = norm_name.split(',')[0].strip()
    
    # Limpieza final común (replicando la lógica JS)
    if norm_name:
        # limitando tamaño del nombre para normas con nombre muy extenso
        norm_name = norm_name[:235]
        # Reemplazar todos los / por -
        norm_name = re.sub(r'\/', '-', norm_name)
        # Reemplazar 'n°' o 'nº' y otros caracteres por espacio
        norm_name = re.sub(r'n[°º“]', ' ', norm_name.lower())
        # Reemplazar espacios por guiones
        norm_name = norm_name.replace(' ', '-')
        # Colapsar guiones múltiples a uno solo
        norm_name = re.sub(r'-{2,}', '-', norm_name)
        # Eliminar guiones al inicio o final
        norm_name = norm_name.strip('-')
    
    return norm_name
    
