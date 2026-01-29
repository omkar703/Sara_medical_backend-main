# E2E Test Report

Generated: 2026-01-29T11:28:00.992751

## Summary
- Users Created: 10
- Documents Uploaded: 5
- Appointments: 5

## JSON Data Used & API Interactions

```json
[
  {
    "timestamp": "2026-01-29T11:22:26.657994",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_patient1_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Patient 1 Test",
      "role": "patient",
      "date_of_birth": "1980-01-01",
      "phone_number": "+15550000001"
    },
    "status": 201,
    "response": {
      "id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "name": "Patient 1 Test",
      "email": "custom_patient1_1769646146@test.com",
      "first_name": "Patient",
      "last_name": "1 Test",
      "phone_number": "+15550000001",
      "role": "patient",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:26.634290Z",
      "updated_at": "2026-01-29T05:52:26.634292Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:26.893513",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient1_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:27.132416",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_patient2_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Patient 2 Test",
      "role": "patient",
      "date_of_birth": "1980-01-01",
      "phone_number": "+15550000002"
    },
    "status": 201,
    "response": {
      "id": "a7a96efb-82e7-4f91-8fe8-e65f530946ae",
      "name": "Patient 2 Test",
      "email": "custom_patient2_1769646146@test.com",
      "first_name": "Patient",
      "last_name": "2 Test",
      "phone_number": "+15550000002",
      "role": "patient",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:27.122858Z",
      "updated_at": "2026-01-29T05:52:27.122859Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:27.370505",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient2_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:27.608507",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_patient3_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Patient 3 Test",
      "role": "patient",
      "date_of_birth": "1980-01-01",
      "phone_number": "+15550000003"
    },
    "status": 201,
    "response": {
      "id": "4a5eebc8-fff6-4549-9483-0ff7303803d1",
      "name": "Patient 3 Test",
      "email": "custom_patient3_1769646146@test.com",
      "first_name": "Patient",
      "last_name": "3 Test",
      "phone_number": "+15550000003",
      "role": "patient",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:27.599958Z",
      "updated_at": "2026-01-29T05:52:27.599959Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:27.838789",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient3_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:28.080581",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_patient4_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Patient 4 Test",
      "role": "patient",
      "date_of_birth": "1980-01-01",
      "phone_number": "+15550000004"
    },
    "status": 201,
    "response": {
      "id": "a9821820-cf9a-43f0-aa1e-69d9a9cb1bdc",
      "name": "Patient 4 Test",
      "email": "custom_patient4_1769646146@test.com",
      "first_name": "Patient",
      "last_name": "4 Test",
      "phone_number": "+15550000004",
      "role": "patient",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:28.067874Z",
      "updated_at": "2026-01-29T05:52:28.067875Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:28.311547",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient4_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:28.550235",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_patient5_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Patient 5 Test",
      "role": "patient",
      "date_of_birth": "1980-01-01",
      "phone_number": "+15550000005"
    },
    "status": 201,
    "response": {
      "id": "e68d689f-ccee-4447-a4fb-4b9e2352cd08",
      "name": "Patient 5 Test",
      "email": "custom_patient5_1769646146@test.com",
      "first_name": "Patient",
      "last_name": "5 Test",
      "phone_number": "+15550000005",
      "role": "patient",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:28.541082Z",
      "updated_at": "2026-01-29T05:52:28.541083Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:28.783065",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient5_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:29.018902",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor1_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 1 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110001",
      "specialty": "Cardiology",
      "license_number": "LIC-1-1769646146"
    },
    "status": 201,
    "response": {
      "id": "f30140b7-4441-40b9-bbde-1e44dbfe1cee",
      "name": "Dr. 1 Test",
      "email": "custom_doctor1_1769646146@test.com",
      "first_name": "Dr.",
      "last_name": "1 Test",
      "phone_number": "+15551110001",
      "role": "doctor",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:29.009446Z",
      "updated_at": "2026-01-29T05:52:29.009447Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:29.251173",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor1_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:29.485465",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor2_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 2 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110002",
      "specialty": "Dermatology",
      "license_number": "LIC-2-1769646146"
    },
    "status": 201,
    "response": {
      "id": "0666f9d7-eb08-4d1f-9a03-5aaeb4f0f1eb",
      "name": "Dr. 2 Test",
      "email": "custom_doctor2_1769646146@test.com",
      "first_name": "Dr.",
      "last_name": "2 Test",
      "phone_number": "+15551110002",
      "role": "doctor",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:29.476895Z",
      "updated_at": "2026-01-29T05:52:29.476896Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:29.715900",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor2_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:29.952737",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor3_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 3 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110003",
      "specialty": "Pediatrics",
      "license_number": "LIC-3-1769646146"
    },
    "status": 201,
    "response": {
      "id": "66d72768-fbd7-4ece-a76d-e03a2cad8542",
      "name": "Dr. 3 Test",
      "email": "custom_doctor3_1769646146@test.com",
      "first_name": "Dr.",
      "last_name": "3 Test",
      "phone_number": "+15551110003",
      "role": "doctor",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:29.942001Z",
      "updated_at": "2026-01-29T05:52:29.942002Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:30.180385",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor3_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:30.417026",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor4_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 4 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110004",
      "specialty": "Neurology",
      "license_number": "LIC-4-1769646146"
    },
    "status": 201,
    "response": {
      "id": "7abe87d3-4cc8-4f54-9f45-2711a437adba",
      "name": "Dr. 4 Test",
      "email": "custom_doctor4_1769646146@test.com",
      "first_name": "Dr.",
      "last_name": "4 Test",
      "phone_number": "+15551110004",
      "role": "doctor",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:30.406781Z",
      "updated_at": "2026-01-29T05:52:30.406782Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:30.645666",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor4_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:30.896403",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor5_1769646146@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 5 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110005",
      "specialty": "Orthopedics",
      "license_number": "LIC-5-1769646146"
    },
    "status": 201,
    "response": {
      "id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
      "name": "Dr. 5 Test",
      "email": "custom_doctor5_1769646146@test.com",
      "first_name": "Dr.",
      "last_name": "5 Test",
      "phone_number": "+15551110005",
      "role": "doctor",
      "organization_id": "1f3484ee-9f41-42b0-bce7-10d1b5fce31c",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T05:52:30.885747Z",
      "updated_at": "2026-01-29T05:52:30.885749Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:31.279477",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor5_1769646146@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T11:22:31.808482",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "description": "Test upload of CamScanner 1-11-26 13.41.pdf"
    },
    "status": 201,
    "response": {
      "id": "92bed5a1-7bf1-424c-9d4b-0b0aade1f079",
      "file_name": "CamScanner 1-11-26 13.41.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
      "file_size": 7971926,
      "uploaded_at": "2026-01-29T05:52:31.781657Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/6157cecd-b8c0-4a04-8e14-6dfac123232c/0e993a80-e94a-40c1-a3eb-6f8cc19613ad.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055231Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=8f9e4c8aa77611dbb910c05b75a4db4405e4b74c6ba708b5c5a6421ce9e2348d"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:31.862738",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "description": "Test upload of K_V_VENKATARAMAN__report.pdf"
    },
    "status": 201,
    "response": {
      "id": "e7477df9-06b2-4de6-b979-a1dba7388cf5",
      "file_name": "K_V_VENKATARAMAN__report.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "notes": "Test upload of K_V_VENKATARAMAN__report.pdf",
      "file_size": 180811,
      "uploaded_at": "2026-01-29T05:52:31.843472Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/a7a96efb-82e7-4f91-8fe8-e65f530946ae/e06dc471-e297-410a-b112-2dcb744b978e.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055231Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=74834e5051482b796d2becff5b860f64f81a237a751262170b69022a2609c4da"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:31.907222",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "description": "Test upload of Synthetic_Patient_02_es.pdf"
    },
    "status": 201,
    "response": {
      "id": "07cea1a8-b82f-4b53-a564-f77dee6c90e0",
      "file_name": "Synthetic_Patient_02_es.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "notes": "Test upload of Synthetic_Patient_02_es.pdf",
      "file_size": 41238,
      "uploaded_at": "2026-01-29T05:52:31.893886Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/4a5eebc8-fff6-4549-9483-0ff7303803d1/06f6d59f-75f0-4d36-9633-02175396f6a3.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055231Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=a8ba8689a1b5ee488dc1eb85da5ea930971cadc3ef2ef57bf025645a91ae4f59"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:31.950362",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "description": "Test upload of Synthetic_Patient_04_ar.pdf"
    },
    "status": 201,
    "response": {
      "id": "8b0ec267-cfe1-40e9-a96f-d80ae8059c37",
      "file_name": "Synthetic_Patient_04_ar.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "notes": "Test upload of Synthetic_Patient_04_ar.pdf",
      "file_size": 61797,
      "uploaded_at": "2026-01-29T05:52:31.934117Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/a9821820-cf9a-43f0-aa1e-69d9a9cb1bdc/88019f2a-f31a-4dd2-afe2-1136cde4c45c.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055231Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=bb6527b2613702ab2cb721a66354ce3a74da59b7fa6191c92c337c56721234e1"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:31.987022",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "description": "Test upload of Synthetic_Patient_06_hi-1.pdf"
    },
    "status": 201,
    "response": {
      "id": "0b0bb4f9-7496-4c3b-8398-25893c6d2ae3",
      "file_name": "Synthetic_Patient_06_hi-1.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "notes": "Test upload of Synthetic_Patient_06_hi-1.pdf",
      "file_size": 54818,
      "uploaded_at": "2026-01-29T05:52:31.973611Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/e68d689f-ccee-4447-a4fb-4b9e2352cd08/f8d46039-9210-41c3-afbe-3761e37fda2b.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055231Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=497d10d00803485b8a6319a2fa6f1e61f12519f733ef461cf3ea6f4de9c43162"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.022572",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 1 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "18c79a7e-75a2-4c35-97b0-f3e5158dfd71",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        },
        {
          "id": "f30140b7-4441-40b9-bbde-1e44dbfe1cee",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.065136",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "f30140b7-4441-40b9-bbde-1e44dbfe1cee",
      "requested_date": "2026-01-30T05:52:32.022660",
      "reason": "Consultation request from Patient 1 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "f30140b7-4441-40b9-bbde-1e44dbfe1cee",
      "requested_date": "2026-01-30T05:52:32.022660Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "38641d3a-6044-43e7-98ea-898556afabf4",
      "patient_id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.039210Z",
      "updated_at": "2026-01-29T05:52:32.039213Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.095488",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 2 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "7defcacf-ef8d-4b6c-bf16-916121dc0db7",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        },
        {
          "id": "0666f9d7-eb08-4d1f-9a03-5aaeb4f0f1eb",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.121170",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "0666f9d7-eb08-4d1f-9a03-5aaeb4f0f1eb",
      "requested_date": "2026-01-31T05:52:32.095540",
      "reason": "Consultation request from Patient 2 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "0666f9d7-eb08-4d1f-9a03-5aaeb4f0f1eb",
      "requested_date": "2026-01-31T05:52:32.095540Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "737d11ff-a86a-421e-b640-91a4012ae3c6",
      "patient_id": "a7a96efb-82e7-4f91-8fe8-e65f530946ae",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.109196Z",
      "updated_at": "2026-01-29T05:52:32.109198Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.152671",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 3 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "7190c3b7-6d4a-4e0a-8f69-7a1d403130b5",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        },
        {
          "id": "66d72768-fbd7-4ece-a76d-e03a2cad8542",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.182680",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "66d72768-fbd7-4ece-a76d-e03a2cad8542",
      "requested_date": "2026-02-01T05:52:32.152704",
      "reason": "Consultation request from Patient 3 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "66d72768-fbd7-4ece-a76d-e03a2cad8542",
      "requested_date": "2026-02-01T05:52:32.152704Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "46517a25-a846-494b-9fe2-afe82573486d",
      "patient_id": "4a5eebc8-fff6-4549-9483-0ff7303803d1",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.167714Z",
      "updated_at": "2026-01-29T05:52:32.167718Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.212433",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 4 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "9295aa5c-c773-4cd9-b909-d4a018413347",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        },
        {
          "id": "7abe87d3-4cc8-4f54-9f45-2711a437adba",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.238972",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "7abe87d3-4cc8-4f54-9f45-2711a437adba",
      "requested_date": "2026-02-02T05:52:32.212474",
      "reason": "Consultation request from Patient 4 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "7abe87d3-4cc8-4f54-9f45-2711a437adba",
      "requested_date": "2026-02-02T05:52:32.212474Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "110df84d-f0e9-4ebc-bd6c-6213f24c8350",
      "patient_id": "a9821820-cf9a-43f0-aa1e-69d9a9cb1bdc",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.228007Z",
      "updated_at": "2026-01-29T05:52:32.228008Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.270211",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 5 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "76bb6844-5358-41b9-b86c-5e3849ecc46d",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        },
        {
          "id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T11:22:32.297418",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
      "requested_date": "2026-02-03T05:52:32.270248",
      "reason": "Consultation request from Patient 5 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
      "requested_date": "2026-02-03T05:52:32.270248Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "f68c272f-1c8d-4184-bb30-894d42d0e1d3",
      "patient_id": "e68d689f-ccee-4447-a4fb-4b9e2352cd08",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.284248Z",
      "updated_at": "2026-01-29T05:52:32.284251Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:35.220621",
    "method": "POST",
    "endpoint": "/appointments/38641d3a-6044-43e7-98ea-898556afabf4/approve",
    "payload": {
      "appointment_time": "2026-02-03T05:52:32.297585",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "f30140b7-4441-40b9-bbde-1e44dbfe1cee",
      "requested_date": "2026-02-03T05:52:32.297585Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "38641d3a-6044-43e7-98ea-898556afabf4",
      "patient_id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "98930526983",
      "join_url": "https://zoom.us/j/98930526983?pwd=knqbyCLrcLZW1enYW0W21fdNqa6vSB.1",
      "start_url": "https://zoom.us/s/98930526983?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5ODkzMDUyNjk4MyIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjJhMzU4YmFiZWZkNDRjMjdiNTIwYzIyZDY3YTFkOTc5Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2NzMxNTQsImlhdCI6MTc2OTY2NTk1NCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.MGvBzcJLNBu_Y8PgJs-LxzcSZ70WVZ3C2aWVnAqH8lo",
      "meeting_password": "MnaS6C",
      "created_at": "2026-01-29T05:52:32.039210Z",
      "updated_at": "2026-01-29T05:52:35.196741Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:35.256578",
    "method": "PATCH",
    "endpoint": "/appointments/737d11ff-a86a-421e-b640-91a4012ae3c6/status",
    "payload": {
      "status": "declined",
      "doctor_notes": "Cannot make it."
    },
    "status": 200,
    "response": {
      "doctor_id": "0666f9d7-eb08-4d1f-9a03-5aaeb4f0f1eb",
      "requested_date": "2026-01-31T05:52:32.095540Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "737d11ff-a86a-421e-b640-91a4012ae3c6",
      "patient_id": "a7a96efb-82e7-4f91-8fe8-e65f530946ae",
      "status": "declined",
      "doctor_notes": "Cannot make it.",
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T05:52:32.109196Z",
      "updated_at": "2026-01-29T05:52:35.239295Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:37.051741",
    "method": "POST",
    "endpoint": "/appointments/46517a25-a846-494b-9fe2-afe82573486d/approve",
    "payload": {
      "appointment_time": "2026-02-03T05:52:35.256642",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "66d72768-fbd7-4ece-a76d-e03a2cad8542",
      "requested_date": "2026-02-03T05:52:35.256642Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "46517a25-a846-494b-9fe2-afe82573486d",
      "patient_id": "4a5eebc8-fff6-4549-9483-0ff7303803d1",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "99356544455",
      "join_url": "https://zoom.us/j/99356544455?pwd=LyyrlfExuOFMHOmpZWYxTmzzlBstKC.1",
      "start_url": "https://zoom.us/s/99356544455?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5OTM1NjU0NDQ1NSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImRlNzhjZmU0YjgxMzQzZjRhMWFkYWFkYTI0ZWM2ZTRlIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2NzMxNTYsImlhdCI6MTc2OTY2NTk1NiwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.kTeFBu87ADjq6zrilQy7Dr-2_4I6b6qZTO5vubBXiWE",
      "meeting_password": "ns29ZV",
      "created_at": "2026-01-29T05:52:32.167714Z",
      "updated_at": "2026-01-29T05:52:37.040371Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:38.940995",
    "method": "POST",
    "endpoint": "/appointments/110df84d-f0e9-4ebc-bd6c-6213f24c8350/approve",
    "payload": {
      "appointment_time": "2026-02-03T05:52:37.051827",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "7abe87d3-4cc8-4f54-9f45-2711a437adba",
      "requested_date": "2026-02-03T05:52:37.051827Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "110df84d-f0e9-4ebc-bd6c-6213f24c8350",
      "patient_id": "a9821820-cf9a-43f0-aa1e-69d9a9cb1bdc",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "96554368752",
      "join_url": "https://zoom.us/j/96554368752?pwd=ib2aEU6PGTxJ0bbaAUjga5jd4SPRb9.1",
      "start_url": "https://zoom.us/s/96554368752?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NjU1NDM2ODc1MiIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImQ3OTM0ZWM4MmEzZjQ5NjM4ZWY0YzhiYzNjMjA2MzA5Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2NzMxNTgsImlhdCI6MTc2OTY2NTk1OCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.XcBNLDU1VXZWVSy7MVn6iG9PkeJM0GnZyVoiPRbsdgE",
      "meeting_password": "9nMXrN",
      "created_at": "2026-01-29T05:52:32.228007Z",
      "updated_at": "2026-01-29T05:52:38.926190Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:41.375934",
    "method": "POST",
    "endpoint": "/appointments/f68c272f-1c8d-4184-bb30-894d42d0e1d3/approve",
    "payload": {
      "appointment_time": "2026-02-03T05:52:38.941262",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
      "requested_date": "2026-02-03T05:52:38.941262Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "f68c272f-1c8d-4184-bb30-894d42d0e1d3",
      "patient_id": "e68d689f-ccee-4447-a4fb-4b9e2352cd08",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "95025787505",
      "join_url": "https://zoom.us/j/95025787505?pwd=UB8L6ILN4EdmvSx9mGoT31NJxt22E9.1",
      "start_url": "https://zoom.us/s/95025787505?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NTAyNTc4NzUwNSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImU0NGRiODY4ODA4MTQ5NWNiMGMwODdjNzY1OTU4Y2Q0Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2NzMxNjEsImlhdCI6MTc2OTY2NTk2MSwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.PvIZFUEQV90beVHisYAwhwBgQdjtyi7GfbgWlwCIBvM",
      "meeting_password": "1dbiMG",
      "created_at": "2026-01-29T05:52:32.284248Z",
      "updated_at": "2026-01-29T05:52:41.340703Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:41.411462",
    "method": "GET",
    "endpoint": "/doctor/patients/6157cecd-b8c0-4a04-8e14-6dfac123232c/documents",
    "payload": {},
    "status": 200,
    "response": [
      {
        "id": "92bed5a1-7bf1-424c-9d4b-0b0aade1f079",
        "file_name": "CamScanner 1-11-26 13.41.pdf",
        "category": "LAB_REPORT",
        "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
        "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
        "file_size": 7971926,
        "uploaded_at": "2026-01-29T05:52:31.781657Z",
        "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/1f3484ee-9f41-42b0-bce7-10d1b5fce31c/6157cecd-b8c0-4a04-8e14-6dfac123232c/0e993a80-e94a-40c1-a3eb-6f8cc19613ad.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T055241Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=1df431d4b27c69b75014a7aabbc1a945c1df94e8f8bbc2012e7d30013b48959a"
      }
    ]
  },
  {
    "timestamp": "2026-01-29T11:22:41.475624",
    "method": "POST",
    "endpoint": "/doctor/tasks",
    "payload": {
      "title": "General Ward Round",
      "priority": "normal",
      "due_date": "2026-01-30T05:52:41.411634"
    },
    "status": 201,
    "response": {
      "title": "General Ward Round",
      "description": null,
      "due_date": "2026-01-30T05:52:41.411634Z",
      "priority": "normal",
      "status": "pending",
      "id": "8590f290-f5e6-41b3-b2aa-fd106fcb48bf",
      "doctor_id": "ae3794f9-e9e1-4e7a-932d-80ee3e193a73",
      "created_at": "2026-01-29T05:52:41.443037Z",
      "updated_at": "2026-01-29T05:52:41.443039Z"
    }
  },
  {
    "timestamp": "2026-01-29T11:22:41.742622",
    "method": "POST",
    "endpoint": "/doctor/ai/process-document",
    "payload": {
      "patient_id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "document_id": "92bed5a1-7bf1-424c-9d4b-0b0aade1f079",
      "processing_type": "comprehensive",
      "priority": "normal"
    },
    "status": 201,
    "response": {
      "job_id": "eafadfc6-eb9f-4b3a-b58d-2d72b6658772",
      "status": "pending",
      "message": "Document queued for AI processing. Job ID: eafadfc6-eb9f-4b3a-b58d-2d72b6658772"
    }
  },
  {
    "timestamp": "2026-01-29T11:27:50.505578",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/patient",
    "payload": {
      "patient_id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "query": "What does my report say about heart rate?",
      "document_id": "92bed5a1-7bf1-424c-9d4b-0b0aade1f079"
    },
    "status": 200,
    "response": "Unfortunately, none of the provided medical record sources mention anything about heart rate or contain information related to assessing the patient's heart rate. The reports focus on laboratory test results for blood markers, proteins, electrolytes, inflammation, hematological indices, as well as some imaging findings from a chest X-ray and PET CT scan. However, there is no specific data pertaining to the patient's heart rate measurements.\n\nI do not have enough information from the given context to comment on the patient's heart rate. As an AI assistant without direct access to the patient's complete medical records and clinical context, I cannot provide any professional medical advice. Please consult a qualified healthcare provider for an accurate assessment and appropriate medical guidance regarding the patient's condition and test results interpretation."
  },
  {
    "timestamp": "2026-01-29T11:28:00.992580",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/doctor",
    "payload": {
      "patient_id": "6157cecd-b8c0-4a04-8e14-6dfac123232c",
      "query": "Summarize this patient's condition.",
      "document_id": "92bed5a1-7bf1-424c-9d4b-0b0aade1f079"
    },
    "status": 200,
    "response": "Based on the provided context from the medical records, here is a summary of the patient's condition:\n\nThe patient, Mr. K V VENKATARAMAN, was admitted to TriLife Hospital with severe back pain, inability to mobilize, radiating pain in the lower limbs, and inability to tolerate pain. He was found to have pathological fractures of the T7, T12, and L4 vertebrae, along with a diagnosis of multiple myeloma, which is a type of cancer affecting plasma cells in the bone marrow.\n\nInvestigations and procedures performed during the hospital stay included:\n\n1. Urine routine test showing pus cells, suggesting a urinary tract infection.\n2. Elevated creatinine levels (1.6 mg/dl) and low potassium levels (2.7 mEq/L).\n3. PET CT scan and oncologist consultation for suspected multiple myeloma.\n4. Bone marrow aspiration and biopsy, which confirmed morphological features consistent with plasma cell neoplasm (cancer).\n5. Nephrologist consultation due to increased creatinine levels.\n6. Sputum culture showing Klebsiella pneumoniae infection and gram stain revealing pus cells.\n7. Urine culture growing heavy Escherichia coli.\n8. Treatment with intravenous antibiotics, diuretics, and other supportive care.\n\nThe discharge summary mentions the patient was conscious, oriented, and vitals were stable at the time of discharge. Medications prescribed included antibiotics, steroids, nebulizers, and others. Follow-up appointments were advised with orthopedics, specific doctors, and for pending test reports and chest X-ray.\n\nDisclaimer: I am an AI assistant. This summary is based on the provided context and should not be considered professional medical advice. Always consult with qualified healthcare professionals for any medical concerns or treatment decisions."
  }
]
```
