# Medical OCR Backend - Quick Test Guide

## 🎉 System is Running!

All services are up and healthy:

- ✅ FastAPI server on http://localhost:8000
- ✅ Redis broker on localhost:6379
- ✅ Celery worker processing tasks
- ✅ Flower monitoring on http://localhost:5555

## 🧪 Test the API

### 1. Check Service Status

```bash
curl http://localhost:8000/ | jq
```

**Expected:**

```json
{
  "service": "Medical OCR Extraction API",
  "version": "1.0.0",
  "mode": "cpu-only"
}
```

### 2. Check Health

```bash
curl http://localhost:8000/health | jq
```

**Expected:**

```json
{
  "status": "healthy",
  "redis": "connected",
  "celery": "running"
}
```

### 3. View API Documentation

Open in your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Test OCR Extraction (Create a Test File First)

**Create a simple test image with text:**

```bash
# Install imagemagick if needed
sudo apt-get install imagemagick

# Create a test image with medical-like text
convert -size 800x600 xc:white \
  -font Arial -pointsize 24 -fill black \
  -annotate +50+100 "Patient Name: John Doe" \
  -annotate +50+150 "Age: 45 years" \
  -annotate +50+200 "Gender: Male" \
  -annotate +50+250 "BP: 120/80 mmHg" \
  -annotate +50+300 "Heart Rate: 72 bpm" \
  -annotate +50+350 "Glucose: 95 mg/dL" \
  -annotate +50+400 "Medication: Metformin 500mg twice daily" \
  test_prescription.png
```

**Or use any existing PDF/image file you have!**

**Upload and extract:**

```bash
curl -X POST http://localhost:8000/ocr/extract \
  -F "file=@test_prescription.png" \
  -F "output_format=json" \
  | jq
```

**Expected Response:**

```json
{
  "status": "completed",
  "file_name": "test_prescription.png",
  "pages": [
    {
      "page_number": 1,
      "text": "Patient Name: John Doe...",
      "confidence": 0.92,
      "entities": [...]
    }
  ],
  "entities": [
    {
      "entity_type": "patient_name",
      "value": "John Doe",
      "confidence": 0.9
    },
    {
      "entity_type": "vital_sign",
      "value": "120/80",
      "unit": "mmHg"
    }
    // ... more entities
  ],
  "overall_confidence": 0.92
}
```

### 5. Test FHIR Output

```bash
curl -X POST "http://localhost:8000/ocr/extract?output_format=fhir" \
  -F "file=@test_prescription.png" \
  | jq '.fhir_bundle'
```

This will return FHIR R4 compliant resources!

### 6. Test Batch Upload

```bash
curl -X POST http://localhost:8000/ocr/batch \
  -F "files=@file1.png" \
  -F "files=@file2.pdf" \
  | jq
```

**Response:**

```json
{
  "batch_id": "batch-abc123",
  "status": "queued",
  "total_files": 2
}
```

### 7. Check Task Status

```bash
# If you got a task_id from async processing:
curl http://localhost:8000/tasks/YOUR_TASK_ID | jq
```

## 📊 Monitor Services

### View Logs

```bash
# API logs
docker compose logs -f api

# Worker logs
docker compose logs -f worker

# All logs
docker compose logs -f
```

### Check Celery Tasks

Open Flower monitoring dashboard:
http://localhost:5555

### Container Status

```bash
docker compose ps
```

## 🛑 Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## 🔄 Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart api
```

## 📝 Next Steps

1. **Test with real medical documents** (prescriptions, lab reports)
2. **Customize medical entity patterns** in `app/utils/regex_patterns.py`
3. **Add more FHIR resources** as needed
4. **Implement authentication** for production
5. **Configure for production deployment**

## 🐛 Troubleshooting

**Services won't start?**

```bash
docker compose logs api
docker compose logs worker
```

**Low OCR accuracy?**

- Ensure images are high quality (300 DPI recommended)
- Images should be clear, not blurry
- Text should be horizontal (auto-deskew helps but not perfect)

**Celery tasks not processing?**

```bash
# Check worker is running
docker compose logs worker

# Check Redis
docker compose logs redis
```

---

**Built with ❤️ - Your Medical OCR Backend is Ready!** 🏥
