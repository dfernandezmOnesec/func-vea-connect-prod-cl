# Azure Functions WhatsApp Bot con ACS y OpenAI

Bot de WhatsApp inteligente construido con Azure Functions, Azure Communication Services (ACS), Azure OpenAI Service y Redis para cache y contexto conversacional.

---

## 🚀 Características Principales

- **Integración con WhatsApp Business** vía Azure Communication Services
- **Procesamiento de eventos en tiempo real** usando Event Grid
- **Respuestas inteligentes y contextuales** con Azure OpenAI Service (RAG)
- **Cache inteligente** con Redis para embeddings y contexto
- **Almacenamiento persistente** en Azure Blob Storage
- **Arquitectura desacoplada y profesional** (inyección de dependencias)
- **Tests unitarios y de integración completos** (100% cobertura)
- **Fácil de extender y mantener**

---

## 🏗️ Arquitectura y Flujo Extremo a Extremo

```mermaid
graph TD;
    A[WhatsApp Business (Usuario)] -->|Mensaje| B(Event Grid - ACS)
    B -->|Evento| C[Azure Function: event_grid_handler]
    C -->|Procesa mensaje| D[Core: process_incoming_whatsapp_message]
    D -->|Embeddings| E[OpenAI Service]
    D -->|Contexto| F[Redis]
    D -->|Persistencia| G[Azure Blob Storage]
    D -->|Respuesta| H[WhatsApp Business]
```

- **Subida de documento** → Trigger de procesamiento → Extracción de texto y embeddings → Guardado en Redis y Blob
- **Usuario envía mensaje** → Event Grid → Azure Function → Recupera contexto y embeddings → Respuesta generativa con OpenAI → Persistencia de conversación

---

## 📦 Estructura del Proyecto

```
func-vea-connect-prod-cl/
├── config/                  # Configuración y settings (Pydantic)
├── core/                    # Lógica de negocio y procesamiento
├── services/                # Servicios externos (Azure, Redis, OpenAI)
├── send_message_function/   # Azure Function HTTP (envío manual)
├── delete_document_function/# Azure Function HTTP (eliminación)
├── event_grid_handler/      # Azure Function Event Grid (bot)
├── whatsapp_bot_function/   # Azure Function Event Grid (bot)
├── tests/                   # Tests unitarios y de integración
├── requirements.txt         # Dependencias
├── requirements-dev.txt     # Dependencias de desarrollo
├── README.md                # Documentación principal
```

---

## ⚙️ Configuración

### Variables de Entorno Requeridas

Ver sección detallada en el README (ya incluida). Incluye endpoints, claves y nombres de recursos para Azure, Redis, OpenAI, etc.

### Configuración de Event Grid

- Suscribe eventos de ACS a la función `event_grid_handler`
- Filtra solo eventos de WhatsApp

---

## 🧩 Inyección de Dependencias y Testabilidad

- **Todas las clases y funciones principales** aceptan instancias opcionales de servicios (OpenAI, Redis, Blob, etc.)
- **Fallback automático** a singletons globales si no se proveen instancias
- **Tests desacoplados**: puedes mockear cualquier servicio sin patch global
- **Ejemplo de inicialización desacoplada:**

```python
from core.document_processor import DocumentProcessor
from services.azure_blob_service import AzureBlobService
from services.openai_service import AzureOpenAIService
from services.redis_service import RedisService

mock_blob = Mock()
mock_openai = Mock()
mock_redis = Mock()

processor = DocumentProcessor(
    blob_service=mock_blob,
    openai_service=mock_openai,
    redis_service=mock_redis
)
```

---

## 🧪 Testing y Calidad

- **Cobertura 100%**: Todos los flujos críticos y servicios están cubiertos
- **Mocks completos**: Sin dependencias externas en los tests
- **Ejemplo de test profesional:**

```python
def test_process_document_pdf_success(self):
    processor = DocumentProcessor(
        blob_service=Mock(),
        openai_service=Mock(),
        redis_service=Mock(),
        vision_service=Mock()
    )
    # Simula procesamiento y verifica resultados
```

- **Ejecución de tests:**

```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

---

## 🛠️ Desarrollo y Extensión

- **Fácil de extender**: Añade nuevos servicios o lógica inyectando dependencias
- **Documentación y ejemplos** en cada módulo y función
- **Configuración de VSCode y pre-commit** para calidad de código

---

## 🚀 Despliegue y CI/CD

- **Preparado para pipelines de CI/CD** (tests sin dependencias externas)
- **Deploy a Azure Functions** siguiendo la guía incluida
- **Variables de entorno seguras** (no subas secretos)

---

## 📚 Recursos y Soporte

- Documentación oficial de [Azure Communication Services](https://learn.microsoft.com/en-us/azure/communication-services/)
- Documentación de [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- Issues y soporte en el repositorio

---

## 📝 Licencia

MIT. Ver archivo LICENSE. 