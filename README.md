# Medical OCR & Data Extraction Backend

Production-grade, **CPU-optimized** OCR and medical data extraction service built with FastAPI, Tesseract OCR, Celery, and Redis.

## 🚀 Features

- ✅ **CPU-only processing** - No GPU dependencies
- 📄 **Multi-format support** - PDF and images (PNG, JPG, JPEG)
- 🔍 **Medical entity extraction** - Medications, vitals, lab values, patient info
- 🏥 **FHIR R4 compliant** - Healthcare interoperability standard
- ⚡ **Background processing** - Celery + Redis for large files
- 🐳 **Docker containerized** - Isolated environment
- 📊 **High accuracy** - Advanced image preprocessing with OpenCV
- 🔒 **Production-ready** - Comprehensive error handling and validation

## 🏗️ Architecture

```
Client → FastAPI Gateway → File Validation
                ↓
        Async/Sync Decision
                ↓
    ┌───────────┴───────────┐
    │                       │
Sync (Small)          Async (Large)
    │                       │
    ↓                       ↓
OCR Service         Celery Task Queue
    │                       │
    └───────────┬───────────┘
                ↓
        Medical Extraction
                ↓
        FHIR Mapping (Optional)
                ↓
        JSON/FHIR Response
```

## 🛠️ Tech Stack

- **FastAPI** - Modern async web framework
- **Tesseract OCR** - Industry-standard OCR engine
- **OpenCV** - Image preprocessing
- **Celery** - Distributed task queue
- **Redis** - Message broker and result backend
- **Pydantic** - Data validation
- **FHIR Resources** - Healthcare data standards
- **Docker** - Containerization

## 📋 Prerequisites

- Python 3.11+
- UV package manager
- Docker & Docker Compose (for isolated environment)
- Tesseract OCR (installed in Docker)

## 🚀 Quick Start

### Option 1: Using UV Virtual Environment

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Copy environment file
cp .env.example .env

# Install system dependencies (Tesseract, Poppler)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils

# Run Redis (required)
docker run -d -p 6379:6379 redis:7-alpine

# Start Celery worker
celery -A app.workers.celery_worker worker --loglevel=info &

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Using Docker (Recommended - Isolated Environment)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The API will be available at:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555

## 📡 API Endpoints

### Root Endpoint

```bash
GET /
```

Returns service information.

### Health Check

```bash
GET /health
```

Check Redis and Celery worker status.

### Single File OCR

```bash
POST /ocr/extract
```

**Parameters:**

- `file` (form-data): PDF or image file
- `output_format` (query): `json` or `fhir` (default: `json`)
- `extract_entities` (query): `true` or `false` (default: `true`)

**Example:**

```bash
curl -X POST http://localhost:8000/ocr/extract \
  -F "file=@prescription.pdf" \
  -F "output_format=json" \
  | jq
```

**Response (small files):**

```json
{
  "status": "completed",
  "file_name": "prescription.pdf",
  "pages": [...],
  "entities": [...],
  "overall_confidence": 0.92,
  "processing_time_ms": 1234.5
}
```

**Response (large files):**

```json
{
  "task_id": "abc-123-def",
  "status": "queued",
  "file_name": "large_report.pdf"
}
```

### Batch Upload

```bash
POST /ocr/batch
```

Upload multiple files for batch processing.

**Example:**

```bash
curl -X POST http://localhost:8000/ocr/batch \
  -F "files=@file1.pdf" \
  -F "files=@file2.jpg" \
  -F "files=@file3.png"
```

### Task Status

```bash
GET /tasks/{task_id}
```

Check status of background task.

**Example:**

```bash
curl http://localhost:8000/tasks/abc-123-def | jq
```

## 🏥 Medical Entity Extraction

The system automatically extracts:

### Patient Information

- Name
- Age
- Gender
- Medical Record Number (MRN)

### Medications

- Drug names
- Dosages (mg, ml, mcg, IU)
- Frequencies (QD, BID, TID, daily, etc.)

### Vital Signs

- Blood Pressure (systolic/diastolic)
- Heart Rate (bpm)
- Temperature (°C/°F)
- SpO2 (%)
- Weight, Height

### Laboratory Values

- Glucose (mg/dL)
- HbA1c (%)
- Cholesterol (LDL, HDL, Total)
- Creatinine
- Hemoglobin
- WBC count

### Dates

- Multiple date formats supported

## 🔧 Configuration

Edit `.env` file or set environment variables:

```bash
# Application
APP_NAME=Medical OCR Extraction API
APP_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000

# Redis
REDIS_URL=redis://localhost:6379/0

# File Limits
MAX_FILE_SIZE_MB=50
MAX_BATCH_SIZE=50
ASYNC_THRESHOLD_MB=5

# OCR
TESSERACT_LANG=eng
OCR_CONFIG=--oem 3 --psm 6
```

## 🧪 Testing

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📊 Performance

- **Small files (<5MB)**: Synchronous processing (~1-3 seconds)
- **Large files (>=5MB)**: Asynchronous processing (background)
- **Multi-page PDFs**: Page-wise processing for efficiency
- **Batch uploads**: Parallel processing via Celery workers

## 🔒 Security Considerations

- ✅ No GPU - Eliminates CUDA security risks
- ✅ File type validation
- ✅ File size limits
- ✅ Filename sanitization
- ✅ Non-root Docker user
- ⚠️ Configure CORS appropriately for production
- ⚠️ Add authentication/authorization as needed
- ⚠️ Ensure HIPAA/GDPR compliance for medical data

## 📝 FHIR Output

When `output_format=fhir`, the API returns FHIR R4 compliant resources:

- **Patient** - Demographics
- **Observation** - Vitals and lab values
- **MedicationStatement** - Current medications
- **DiagnosticReport** - Overall report wrapper
- **Bundle** - Collection of all resources

## 🐛 Troubleshooting

### Tesseract not found

```bash
# Docker: Already included
# Local: Install Tesseract
sudo apt-get install tesseract-ocr
```

### Redis connection failed

```bash
# Check Redis is running
docker-compose ps redis
# Or locally:
redis-cli ping
```

### Celery worker not responding

```bash
# Check worker status
docker-compose logs worker
# Or locally:
celery -A app.workers.celery_worker inspect active
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Celery Flower**: http://localhost:5555

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Tesseract OCR by Google
- FastAPI framework
- Celery distributed task queue
- FHIR specification by HL7

## 📧 Support

For issues and questions:

- Create GitHub issue
- Email: dev@liomonk.com

---

**Built with ❤️ for Healthcare by Liomonk**
