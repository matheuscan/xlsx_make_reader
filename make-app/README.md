# Custom app de Make: "XLSX Reader"

Definición en formato **Apps SDK** de la custom app que consume esta API.

```
make-app/
├── app.json                              # metadatos de la app
├── communication.json                    # Base: baseUrl, header X-API-Key, manejo de errores
├── authenticate/api-key.json             # conexión Basic (API key + Base URL)
├── modules/parse-excel/parse-excel.json  # módulo search: sube el binario e itera los bundles
└── rpcs/get-columns/get-columns.json     # RPC de campos dinámicos (columnas del Excel)
```

## Cómo usarla

Make no importa zips directamente; tienes dos opciones:

### Opción A — Editor web de Make (más sencilla)

1. Despliega la API en una URL **HTTPS pública** (ngrok/cloudflared para pruebas).
2. En Make: **Custom apps → Create a new app**. Label: `XLSX Reader`, ID: `xlsx-reader`.
3. **Base**: pega el contenido de `communication.json`.
4. **Connections → Create**: pega el contenido de `authenticate/api-key.json`
   (cada sección del JSON corresponde a una pestaña del editor: Parameters, Communication…).
5. **Modules → Create** `parse-excel`: pega el contenido de
   `modules/parse-excel/parse-excel.json` en sus pestañas correspondientes.
6. **Remote procedures → Create** `get-columns`: pega
   `rpcs/get-columns/get-columns.json`.
7. Crea una conexión (Base URL + API Key) y prueba el módulo.

### Opción B — Apps SDK para VS Code

1. Instala la extensión **Apps SDK** de Make en VS Code y genera tu API key
   en Make (zona de desarrollador de tu organización).
2. Crea una app nueva con ID `xlsx-reader`.
3. Clona la app a tu workspace (`Clone to Local Folder`) y sustituye los
   archivos generados por los de esta carpeta `make-app/`.
4. Sube los cambios (`Deploy to server`).

## Uso en un escenario

1. Añade el módulo **XLSX Reader → Parse Excel File**.
2. En *File name* / *File data* mapea un archivo binario de un módulo anterior
   (p. ej. Google Drive *Download a file*, un webhook con archivo, etc.).
   Make mostrará el diálogo de selección de archivo si los módulos anteriores
   exponen `semantic: file:name` / `file:data`.
3. Al configurar el módulo, el RPC **get-columns** te pedirá un archivo de
   muestra para generar los campos de salida (las columnas del Excel).
4. Cada fila del Excel saldrá como un **bundle** independiente:
   `bundles[0] → operación 1`, `bundles[1] → operación 2`, etc.
5. Ajusta *Sheet* (nombre o índice), *Header row* y *Limit* según tu archivo.

## Notas

- Los valores de celda se devuelven serializados (fechas en ISO 8601, celdas
  vacías como `null`); el RPC declara todas las columnas como `text`, que es el
  tipo más seguro para columnas dinámicas.
- Si cambias la estructura del Excel de muestra, vuelve a ejecutar el módulo y
  regenera la interfaz (el botón "Download output bundles" del inspector de Make
  ayuda a actualizar el interface).
- El header `X-API-Key` se sanea en los logs (`log.sanitize` en el Base).
