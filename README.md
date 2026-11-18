# ¿Cuándo actuar? Sentimiento de las reseñas de Amazon de Serene Herbs

Trabajo final de Analítica de Negocios (Escuela de Administración, EAFIT). Propuesta de un modelo de analítica de negocios: leer el sentimiento de las reseñas de Amazon para decidir cuándo revisar el lote o al proveedor y a qué clientes responder.

## Cómo reproducirlo
1. Abrir `Trabajo_Final_Resenas.ipynb` en Google Colab. Como el repositorio es privado, guardar un token de GitHub con permiso de lectura en **Secretos** de Colab con el nombre `GITHUB_TOKEN`.
2. Entorno de ejecución → **Ejecutar todo**. La primera celda clona este repositorio (variable `REPO_URL`) e instala lo que falta.

## Contenido
| Carpeta o archivo | Qué hay |
|---|---|
| `Trabajo_Final_Resenas.ipynb` | Notebook ejecutado de principio a fin, con el texto de cada etapa |
| `data/` | Datos originales tal como se descargaron (`crudo_chrome_apify/`, `bundle_xlsx_historico/`), base preparada, muestra etiquetada a mano y léxico. **Ficha de procedencia en `data/README_datos.md`** |
| `src/` | Código (Python) y pruebas (`src/tests/`) |
| `resultados/` | Tablas y figuras que el notebook exporta |
| `docs/` | Guía de entregables y referencias APA |

Entorno: Python 3, versiones exactas en `requirements.txt`. Pruebas: `python -m unittest discover -s src/tests`.
