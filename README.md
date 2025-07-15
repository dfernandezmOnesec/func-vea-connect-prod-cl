# Azure Functions WhatsApp Bot con ACS y OpenAI

Bot de WhatsApp inteligente construido con Azure Functions, Azure Communication Services (ACS), Azure OpenAI Service y Redis para cache y contexto conversacional.

## Características Principales

- **Integración con WhatsApp Business** a través de Azure Communication Services
- **Procesamiento de eventos en tiempo real** usando Event Grid
- **Generación de respuestas inteligentes** con Azure OpenAI Service
- **RAG (Retrieval-Augmented Generation)** para respuestas contextuales
- **Cache inteligente** con Redis para embeddings y contexto conversacional
- **Almacenamiento persistente** en Azure Blob Storage
- **Arquitectura modular** y escalable
- **Tests unitarios completos**

## Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │───▶│  Event Grid      │───▶│ Azure Functions │
│   Business      │    │  (ACS Events)    │    │  (Python 3.10)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Azure OpenAI    │◀───│   Core Logic     │───▶│   Redis Cache   │
│   Service       │    │   (RAG + Chat)   │    │  (Context +     │
└─────────────────┘    └──────────────────┘    │   Embeddings)   │
                                               └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Azure Blob      │
                                               │ Storage         │
                                               │ (Conversations) │
                                               └─────────────────┘
```

## Estructura del Proyecto

```
func-vea-connect-prod-cl/
├── config/                     # Configuración y settings
│   ├── __init__.py
│   └── settings.py            # Configuración con Pydantic
├── core/                      # Lógica de negocio
│   ├── __init__.py
│   └── embedding_manager.py   # Gestor de embeddings y RAG
├── services/                  # Servicios externos
│   ├── __init__.py
│   ├── acs_service.py         # Azure Communication Services
│   ├── openai_service.py      # Azure OpenAI Service
│   ├── azure_blob_service.py  # Azure Blob Storage
│   ├── redis_service.py       # Redis Cache
│   └── computer_vision_service.py # Computer Vision
├── functions/                 # Azure Functions
│   ├── __init__.py
│   ├── whatsapp_bot_function.py # Event Grid Trigger (WhatsApp Bot)
│   ├── whatsapp_bot_function/   # Function folder
│   │   └── function.json      # Event Grid binding
│   ├── event_grid_handler.py  # Event Grid Trigger (Document Processing)
│   ├── send_message_function.py # HTTP Trigger (envío)
│   └── delete_document_function/ # HTTP Trigger (eliminación de documentos)
│       ├── __init__.py
│       ├── function.json
│       └── README.md
├── tests/                     # Tests unitarios
│   ├── __init__.py
│   ├── conftest.py
│   ├── functions/
│   │   ├── __init__.py
│   │   ├── test_event_grid_handler.py
│   │   ├── test_send_message_function.py
│   │   └── test_delete_document_function.py
│   └── services/
│       ├── __init__.py
│       ├── test_acs_service.py
│       ├── test_openai_service.py
│       ├── test_azure_blob_service.py
│       ├── test_redis_service.py
│       └── test_computer_vision_service.py
├── host.json                  # Configuración de Azure Functions
├── local.settings.json        # Variables de entorno locales
├── requirements.txt           # Dependencias de Python
├── .funcignore               # Archivos a ignorar en deployment
└── README.md                 # Documentación
```

## Configuración

### Variables de Entorno Requeridas

```bash
# Azure OpenAI Service
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment

# Redis Cache
REDIS_CONNECTION_STRING=redis://username:password@host:port
REDIS_CACHE_TTL=3600
EMBEDDING_CACHE_TTL=86400

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=conversations

# Computer Vision
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_API_KEY=your-api-key

# Azure Communication Services
AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING=endpoint=https://...
AZURE_COMMUNICATION_SERVICES_PHONE_NUMBER=+1234567890

# Cola de Procesamiento
AZURE_STORAGE_QUEUE_NAME=message-processing-queue

# Configuración General
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Configuración de Event Grid

El bot utiliza Event Grid para recibir eventos de WhatsApp desde ACS:

1. **Eventos Soportados:**
   - `Microsoft.Communication.AdvancedMessageReceived` - Mensajes entrantes de WhatsApp
   - `Microsoft.Communication.AdvancedMessageDeliveryReportReceived` - Reportes de entrega

2. **Configuración de Suscripción:**
   - Crear suscripción de Event Grid en ACS
   - Configurar endpoint hacia la Azure Function `event_grid_handler`
   - Filtrar solo eventos de WhatsApp

## Funcionalidades

### 1. Procesamiento de Mensajes WhatsApp

- **Recepción automática** de mensajes a través de Event Grid
- **Validación de canal** (solo WhatsApp, no SMS)
- **Extracción de metadatos** (número, contenido, timestamp, ID)

### 2. Generación de Respuestas con RAG

- **Embeddings automáticos** del mensaje del usuario
- **Búsqueda de contenido similar** en base de conocimientos
- **Contexto conversacional** con historial de mensajes
- **Respuestas contextuales** usando Azure OpenAI Service

### 3. Gestión de Contexto Conversacional

- **Cache en Redis** para contexto activo (últimos 20 mensajes)
- **Almacenamiento persistente** en Azure Blob Storage
- **Fallback inteligente** entre Redis y Blob Storage
- **TTL configurable** para optimizar recursos

### 4. Cache Inteligente

- **Cache de embeddings** para mejorar rendimiento
- **Cache de contexto** para conversaciones activas
- **TTL diferenciado** por tipo de contenido
- **Invalidación automática** basada en tiempo

### 5. Gestión de Documentos

- **Eliminación completa** de documentos desde todos los servicios
- **Sincronización automática** entre Azure Storage, Redis y embeddings
- **API REST** para eliminación programática
- **Logging detallado** de operaciones de eliminación

## Uso

### Desarrollo Local

1. **Instalar dependencias de producción:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Instalar dependencias de desarrollo (opcional):**
   ```bash
   pip install -r requirements-dev.txt
   ```
   
   Las dependencias de desarrollo incluyen:
   - `pytest` - Framework de testing
   - `pytest-mock` - Mocks para tests
   - `pytest-cov` - Cobertura de código
   - `httpx` - Cliente HTTP para tests
   - `black` - Formateador de código
   - `flake8` - Linter de código
   - `mypy` - Verificación de tipos

3. **Configurar variables de entorno:**
   ```bash
   cp local.settings.json.example local.settings.json
   # Editar local.settings.json con tus credenciales reales
   # ⚠️ IMPORTANTE: Nunca subas local.settings.json al repositorio
   ```

4. **Ejecutar tests:**
   ```bash
   # Ejecutar todos los tests
   pytest tests/ -v
   
   # Ejecutar tests específicos
   pytest tests/services/ -v
   pytest tests/functions/ -v
   
   # Ejecutar con cobertura
   pytest tests/ --cov=. --cov-report=html
   ```

5. **Ejecutar localmente:**
   ```bash
   func start
   ```

### Deployment

1. **Crear recursos en Azure:**
   - Azure Communication Services
   - Azure OpenAI Service
   - Redis Cache
   - Azure Storage Account
   - Computer Vision (opcional)

2. **Configurar Event Grid:**
   - Suscribir eventos de ACS a la función
   - Configurar filtros para WhatsApp

3. **Deploy a Azure:**
   ```bash
   az functionapp deployment source config-zip \
     --resource-group your-rg \
     --name your-function-app \
     --src .python_packages/lib/python3.10/site-packages/
   ```

## API Endpoints

### Event Grid Handler
- **Trigger:** Event Grid
- **Función:** `event_grid_handler`
- **Propósito:** Procesar eventos de WhatsApp desde ACS

### Send Message Function
- **Trigger:** HTTP POST
- **Endpoint:** `/api/send-message`
- **Propósito:** Enviar mensajes manualmente

```json
POST /api/send-message
{
  "to": "+1234567890",
  "message": "Hello from the bot!"
}
```

### Send WhatsApp Template Function
- **Trigger:** HTTP POST
- **Endpoint:** `/api/send-whatsapp-template`
- **Propósito:** Enviar mensajes de plantilla de WhatsApp (template)

```json
POST /api/send-whatsapp-template
{
  "to_number": "+521234567890",
  "template_name": "vea_info_donativos",
  "template_language": "es_MX",
  "parameters": ["Juan"]
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "WhatsApp template message sent successfully.",
  "to_number": "+521234567890",
  "template_name": "vea_info_donativos",
  "message_id": "xxxx-xxxx-xxxx",
  "timestamp": "2024-07-14T00:00:00.000Z"
}
```

### Delete Document Function
- **Trigger:** HTTP DELETE
- **Endpoint:** `/api/delete-document`
- **Propósito:** Eliminar documentos de todos los servicios

```json
DELETE /api/delete-document
{
  "document_id": "documento_123_abc12345",
  "blob_name": "documents/mi_documento.pdf"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "deletion_details": {
    "storage_deleted": true,
    "redis_deleted": true,
    "embeddings_deleted": true
  }
}
```

## Seguridad

### ⚠️ Protección de Secretos

**NUNCA** subas archivos con secretos reales al repositorio:

- ✅ `local.settings.json.example` - Archivo de ejemplo (sin secretos reales)
- ❌ `local.settings.json` - Archivo con secretos reales (incluido en .gitignore)
- ❌ `.env` - Archivo de variables de entorno (incluido en .gitignore)

### Si accidentalmente subiste secretos:

1. **Inmediatamente** revoca las claves comprometidas en Azure Portal
2. **Genera nuevas claves** para todos los servicios
3. **Actualiza** tu `local.settings.json` con las nuevas claves
4. **Contacta** al administrador del repositorio para limpiar el historial

### Variables de Entorno Seguras

Para desarrollo local, usa `local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AZURE_OPENAI_API_KEY": "tu-clave-real-aqui",
    "AZURE_STORAGE_CONNECTION_STRING": "tu-connection-string-real"
  }
}
```

Para producción, configura las variables en Azure Function App Settings.

## Tests

El proyecto incluye tests unitarios completos con mocks para todos los servicios y funciones:

### Estructura de Tests

```
tests/
├── conftest.py                    # Configuración global de pytest
├── test_whatsapp_bot_function.py  # Tests para WhatsApp Bot Function
├── functions/
│   ├── test_whatsapp_bot_function.py
│   ├── test_event_grid_handler.py
│   ├── test_send_message_function.py
│   └── test_batch_push_results.py
├── services/
│   ├── test_acs_service.py
│   ├── test_openai_service.py
│   ├── test_azure_blob_service.py
│   ├── test_computer_vision_service.py
│   └── test_redis_service.py
└── core/
    ├── test_embedding_manager.py
    └── test_document_processor.py
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests específicos por categoría
pytest tests/functions/ -v
pytest tests/services/ -v
pytest tests/core/ -v

# Ejecutar tests específicos
pytest tests/functions/test_whatsapp_bot_function.py -v
pytest tests/services/test_openai_service.py -v

# Con coverage
pytest tests/ --cov=. --cov-report=html

# Tests con reporte detallado
pytest tests/ -v --tb=short --strict-markers
```

### Características de los Tests

- **Mocks completos**: Todos los servicios externos están mockeados (Redis, OpenAI, Azure Blob Storage, ACS, Computer Vision)
- **Sin dependencias externas**: Los tests pueden ejecutarse sin conexión a servicios reales
- **Cobertura completa**: Tests para casos de éxito y error en todos los métodos públicos
- **Validación robusta**: Verificación de parámetros, respuestas y manejo de errores
- **Compatibilidad CI/CD**: Preparados para ejecutarse en pipelines de integración continua

### Ejemplos de Tests

#### Test de Servicio (ACS)
```python
def test_send_whatsapp_message_success(self):
    """Test successful WhatsApp message sending."""
    mock_acs_service.send_whatsapp_message.return_value = "msg_12345"
    result = acs_service.send_whatsapp_message("+1234567890", "Hello")
    assert result == "msg_12345"
```

#### Test de Función (WhatsApp Bot)
```python
def test_main_successful_processing(self):
    """Test successful message processing."""
    mock_event.event_type = "Microsoft.Communication.SMSReceived"
    mock_extract.return_value = {"from_number": "+1234567890", "message": "Hello"}
    main(mock_event)
    # Verificar que se llamaron todos los servicios esperados
```

### Configuración de Tests

Los tests usan:
- **pytest**: Framework de testing principal
- **pytest-mock**: Para mocking de dependencias
- **pytest-cov**: Para cobertura de código
- **unittest.mock**: Para mocks avanzados

### Validación de Calidad

```bash
# Ejecutar linting
flake8 . --max-line-length=120 --ignore=E203,W503

# Ejecutar type checking
mypy . --ignore-missing-imports

# Ejecutar tests con coverage mínimo
pytest tests/ --cov=. --cov-fail-under=80
```

## Mejoras Recientes

### Correcciones del Event Grid Handler

✅ **Eventos de WhatsApp Correctos:**
- Cambiado de `SMSReceived` a `AdvancedMessageReceived`
- Cambiado de `SMSDeliveryReportReceived` a `AdvancedMessageDeliveryReportReceived`
- Validación de canal para asegurar solo WhatsApp

✅ **Implementación de RAG:**
- Integración completa con `EmbeddingManager`
- Búsqueda de contenido similar
- Contexto enriquecido para respuestas

✅ **Manejo Mejorado de Contexto:**
- Cache en Redis para contexto activo
- Fallback a Blob Storage
- TTL configurable (24h para contexto, 7 días para estados)

✅ **Arquitectura Robusta:**
- Inyección de dependencias correcta
- Manejo de errores mejorado
- Logs detallados para debugging

## Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:
- Crear un issue en el repositorio
- Revisar la documentación de Azure Communication Services
- Consultar la documentación de Azure OpenAI Service 

## Configuración de Desarrollo

### Configuración de VSCode

El proyecto incluye configuración optimizada para VSCode:

- **Python Interpreter**: Configurado para usar el entorno virtual
- **Linting**: Flake8 con reglas personalizadas
- **Formatting**: Black con línea de 120 caracteres
- **Testing**: Pytest integrado
- **Type Checking**: Pyright con configuración básica

### Resolución de Problemas Comunes

#### Error de Importación de pypdf

Si ves warnings sobre `pypdf` no encontrado:

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verificar instalación:**
   ```bash
   python -c "from pypdf import PdfReader; print('pypdf installed successfully')"
   ```

3. **Configuración de Pyright:**
   El archivo `pyrightconfig.json` está configurado para:
   - Excluir directorios de entorno virtual
   - Usar modo de verificación básico
   - Permitir imports de bibliotecas sin stubs

#### Configuración de Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Verificación de Configuración

```bash
# Verificar que todas las dependencias estén instaladas
pip list

# Verificar configuración de pytest
pytest --version

# Verificar configuración de linting
flake8 --version
black --version
```

### Herramientas de Desarrollo

- **Black**: Formateo de código
- **Flake8**: Linting y estilo
- **MyPy**: Verificación de tipos
- **Pytest**: Testing framework
- **Pre-commit**: Hooks de pre-commit

### Comandos Útiles

```bash
# Formatear código
black .

# Verificar estilo
flake8 .

# Verificar tipos
mypy . --ignore-missing-imports

# Ejecutar tests
pytest tests/ -v

# Ejecutar tests con coverage
pytest tests/ --cov=. --cov-report=html
``` 