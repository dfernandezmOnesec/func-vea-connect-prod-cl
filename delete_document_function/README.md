# Función de Eliminación de Documentos

Esta función de Azure Functions permite eliminar documentos de manera completa desde todos los servicios del sistema.

## Endpoint

```
DELETE /api/delete-document
```

## Autenticación

La función requiere autenticación de nivel "function". Necesitas incluir el código de función en la URL o en el header de autorización.

## Parámetros de Entrada

El cuerpo de la petición debe ser un JSON con al menos uno de los siguientes parámetros:

```json
{
  "document_id": "string",  // ID del documento (opcional si se proporciona blob_name)
  "blob_name": "string"     // Nombre del blob en Azure Storage (opcional si se proporciona document_id)
}
```

### Ejemplos de Petición

**Eliminar por document_id:**
```json
{
  "document_id": "documento_123_abc12345"
}
```

**Eliminar por blob_name:**
```json
{
  "blob_name": "documents/mi_documento.pdf"
}
```

**Eliminar con ambos parámetros:**
```json
{
  "document_id": "documento_123_abc12345",
  "blob_name": "documents/mi_documento.pdf"
}
```

## Respuesta

### Respuesta Exitosa (200)

```json
{
  "success": true,
  "message": "Document deleted successfully",
  "document_id": "documento_123_abc12345",
  "blob_name": "documents/mi_documento.pdf",
  "deletion_details": {
    "storage_deleted": true,
    "redis_deleted": true,
    "embeddings_deleted": true,
    "errors": []
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Respuesta con Errores (500)

```json
{
  "success": false,
  "message": "Failed to delete document completely",
  "document_id": "documento_123_abc12345",
  "blob_name": "documents/mi_documento.pdf",
  "deletion_details": {
    "storage_deleted": true,
    "redis_deleted": false,
    "embeddings_deleted": true,
    "errors": [
      "Failed to delete Redis key: embedding:documento_123_abc12345"
    ]
  },
  "error": "Failed to delete Redis key: embedding:documento_123_abc12345"
}
```

### Errores de Validación (400)

```json
{
  "success": false,
  "message": "Missing required parameters: document_id or blob_name"
}
```

## Servicios que se Eliminan

La función elimina el documento de los siguientes servicios:

1. **Azure Blob Storage**: Elimina el archivo físico del contenedor
2. **Redis**: Elimina embeddings, metadatos y chunks del documento
3. **Embedding Manager**: Elimina las referencias de embeddings

## Códigos de Estado HTTP

- `200`: Eliminación exitosa
- `400`: Parámetros faltantes o inválidos
- `405`: Método HTTP no permitido (solo DELETE)
- `500`: Error interno del servidor

## Ejemplo de Uso con cURL

```bash
curl -X DELETE \
  "https://your-function-app.azurewebsites.net/api/delete-document?code=your-function-key" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "documento_123_abc12345",
    "blob_name": "documents/mi_documento.pdf"
  }'
```

## Ejemplo de Uso con JavaScript

```javascript
const deleteDocument = async (documentId, blobName) => {
  const response = await fetch('/api/delete-document', {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      blob_name: blobName
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('Documento eliminado exitosamente');
  } else {
    console.error('Error al eliminar documento:', result.error);
  }
};
```

## Notas Importantes

1. **Eliminación Completa**: La función intenta eliminar el documento de todos los servicios. Si alguno falla, se reporta en los detalles.

2. **Parámetros Opcionales**: Puedes proporcionar solo `document_id` o solo `blob_name`, pero es recomendable proporcionar ambos para mayor precisión.

3. **Logging**: Todas las operaciones se registran en los logs de Azure Functions para auditoría.

4. **Concurrencia**: La función maneja múltiples peticiones de eliminación de manera segura.

5. **Recuperación**: Una vez eliminado, el documento no se puede recuperar fácilmente. Considera implementar un sistema de backup si es necesario. 