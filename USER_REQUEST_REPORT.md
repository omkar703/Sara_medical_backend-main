# E2E Test Report

Generated: 2026-01-29T23:46:43.236778

## Summary
- Users Created: 10
- Documents Uploaded: 5
- Appointments: 5

## JSON Data Used & API Interactions

```json
[
  {
    "timestamp": "2026-01-29T23:41:23.937287",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor1_1769690483@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 1 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110001",
      "organization_name": "Test Hospital",
      "specialty": "Cardiology",
      "license_number": "LIC-1-1769690483"
    },
    "status": 201,
    "response": {
      "id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
      "name": "Dr. 1 Test",
      "email": "custom_doctor1_1769690483@test.com",
      "first_name": "Dr.",
      "last_name": "1 Test",
      "phone_number": "+15551110001",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T18:11:23.917161Z",
      "updated_at": "2026-01-29T18:11:23.917165Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:24.182798",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor1_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:24.418142",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor2_1769690483@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 2 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110002",
      "organization_name": "Test Hospital",
      "specialty": "Dermatology",
      "license_number": "LIC-2-1769690483"
    },
    "status": 201,
    "response": {
      "id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
      "name": "Dr. 2 Test",
      "email": "custom_doctor2_1769690483@test.com",
      "first_name": "Dr.",
      "last_name": "2 Test",
      "phone_number": "+15551110002",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T18:11:24.413089Z",
      "updated_at": "2026-01-29T18:11:24.413090Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:24.652134",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor2_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:24.885745",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor3_1769690483@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 3 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110003",
      "organization_name": "Test Hospital",
      "specialty": "Pediatrics",
      "license_number": "LIC-3-1769690483"
    },
    "status": 201,
    "response": {
      "id": "d4ee1792-1496-4782-b773-fef4c51353ca",
      "name": "Dr. 3 Test",
      "email": "custom_doctor3_1769690483@test.com",
      "first_name": "Dr.",
      "last_name": "3 Test",
      "phone_number": "+15551110003",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T18:11:24.880371Z",
      "updated_at": "2026-01-29T18:11:24.880372Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:25.118984",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor3_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:25.359258",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor4_1769690483@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 4 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110004",
      "organization_name": "Test Hospital",
      "specialty": "Neurology",
      "license_number": "LIC-4-1769690483"
    },
    "status": 201,
    "response": {
      "id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
      "name": "Dr. 4 Test",
      "email": "custom_doctor4_1769690483@test.com",
      "first_name": "Dr.",
      "last_name": "4 Test",
      "phone_number": "+15551110004",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T18:11:25.347291Z",
      "updated_at": "2026-01-29T18:11:25.347292Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:25.596652",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor4_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:25.835951",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor5_1769690483@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 5 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110005",
      "organization_name": "Test Hospital",
      "specialty": "Orthopedics",
      "license_number": "LIC-5-1769690483"
    },
    "status": 201,
    "response": {
      "id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
      "name": "Dr. 5 Test",
      "email": "custom_doctor5_1769690483@test.com",
      "first_name": "Dr.",
      "last_name": "5 Test",
      "phone_number": "+15551110005",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T18:11:25.829325Z",
      "updated_at": "2026-01-29T18:11:25.829326Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:26.073083",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor5_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:26.333052",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 1 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000001",
      "email": "custom_patient1_1769690483@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 1 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000001",
      "email": "custom_patient1_1769690483@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "mrn": "ORG-2026-000117-0381",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T18:11:26.082603",
      "updated_at": "2026-01-29T18:11:26.082603"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:26.568719",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient1_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:26.814477",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 2 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000002",
      "email": "custom_patient2_1769690483@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 2 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000002",
      "email": "custom_patient2_1769690483@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "dc990553-a24f-4838-8d42-5e43790edb74",
      "mrn": "ORG-2026-000118-2884",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T18:11:26.579917",
      "updated_at": "2026-01-29T18:11:26.579917"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:27.049544",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient2_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:27.293495",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 3 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000003",
      "email": "custom_patient3_1769690483@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 3 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000003",
      "email": "custom_patient3_1769690483@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "3fec6ac8-92d3-4552-b514-353b2ee20522",
      "mrn": "ORG-2026-000119-4978",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T18:11:27.060550",
      "updated_at": "2026-01-29T18:11:27.060550"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:27.525476",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient3_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:27.782171",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 4 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000004",
      "email": "custom_patient4_1769690483@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 4 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000004",
      "email": "custom_patient4_1769690483@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "20e81985-cce8-4af2-afe7-b713e4d8f55e",
      "mrn": "ORG-2026-000120-0534",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T18:11:27.535466",
      "updated_at": "2026-01-29T18:11:27.535466"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.033139",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient4_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:28.274956",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 5 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000005",
      "email": "custom_patient5_1769690483@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 5 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000005",
      "email": "custom_patient5_1769690483@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "64d33677-4106-462b-8580-b3afda1e152b",
      "mrn": "ORG-2026-000121-6059",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T18:11:28.045041",
      "updated_at": "2026-01-29T18:11:28.045041"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.513118",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient5_1769690483@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:41:28.742423",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "description": "Test upload of CamScanner 1-11-26 13.41.pdf"
    },
    "status": 201,
    "response": {
      "id": "759a6391-c83e-41dd-9f40-830593630f96",
      "file_name": "CamScanner 1-11-26 13.41.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
      "file_size": 7971926,
      "uploaded_at": "2026-01-29T18:11:28.727914Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/225b710a-f93a-4f70-86d4-66eff97e5c7d/47fca654-5e85-41f3-8dd5-bb270b703bc0.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181128Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=2739b3e4e7bd62eca1a83c1d4ce41795086e323ac5b0f8abfc650e772cf289e9"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.774044",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "description": "Test upload of K_V_VENKATARAMAN__report.pdf"
    },
    "status": 201,
    "response": {
      "id": "fd066614-c2a6-4903-9373-f21932baac76",
      "file_name": "K_V_VENKATARAMAN__report.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "notes": "Test upload of K_V_VENKATARAMAN__report.pdf",
      "file_size": 180811,
      "uploaded_at": "2026-01-29T18:11:28.765998Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/dc990553-a24f-4838-8d42-5e43790edb74/579dbbe4-64f7-4085-9d9b-e3cdf1a0a558.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181128Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=0e542354c4a080f905e3773fff83c25bddaa032d14cd1d7c8c1e489e46c4dcdf"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.800347",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "description": "Test upload of Synthetic_Patient_02_es.pdf"
    },
    "status": 201,
    "response": {
      "id": "830b28d6-5af7-42f4-9bf2-f37c2860c42b",
      "file_name": "Synthetic_Patient_02_es.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "notes": "Test upload of Synthetic_Patient_02_es.pdf",
      "file_size": 41238,
      "uploaded_at": "2026-01-29T18:11:28.792068Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/3fec6ac8-92d3-4552-b514-353b2ee20522/9d903d4f-949a-4e53-bad5-0a6ccbdeeab1.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181128Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=c463b4cdc67d3ce703cb7553d0d9586b32bebd37695bc257e86f0a965fc60f7b"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.829674",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "description": "Test upload of Synthetic_Patient_04_ar.pdf"
    },
    "status": 201,
    "response": {
      "id": "bdf387b5-5309-487d-9285-916a6b59f2bc",
      "file_name": "Synthetic_Patient_04_ar.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "notes": "Test upload of Synthetic_Patient_04_ar.pdf",
      "file_size": 61797,
      "uploaded_at": "2026-01-29T18:11:28.818430Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/20e81985-cce8-4af2-afe7-b713e4d8f55e/815e7f90-220f-4bfc-932c-f78e9df2b423.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181128Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=be3e94c30f59dc682bcc1a5f69be94b361a22a213708b1998d07fc15cc98db91"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.857889",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "description": "Test upload of Synthetic_Patient_06_hi-1.pdf"
    },
    "status": 201,
    "response": {
      "id": "dcd47e8e-0fb1-4079-ad17-901a7ccd053f",
      "file_name": "Synthetic_Patient_06_hi-1.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "notes": "Test upload of Synthetic_Patient_06_hi-1.pdf",
      "file_size": 54818,
      "uploaded_at": "2026-01-29T18:11:28.849566Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/64d33677-4106-462b-8580-b3afda1e152b/0d24bc71-2e13-43e2-b272-be7166de162b.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181128Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=a9742be76ba8ccedb0ce073a0f231d446149891d203d70bf156a266e08d19de4"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.875259",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.887623",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 1 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.919947",
    "method": "POST",
    "endpoint": "/appointments",
    "payload": {
      "doctor_id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
      "requested_date": "2026-01-30T18:11:28.887703",
      "reason": "Consultation request from Patient 1 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
      "requested_date": "2026-01-30T18:11:28.887703Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "36f3a962-0ff6-4c8a-889b-866e6d61a6bb",
      "patient_id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:28.900266Z",
      "updated_at": "2026-01-29T18:11:28.900268Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.933694",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.948563",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 2 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.967314",
    "method": "POST",
    "endpoint": "/appointments",
    "payload": {
      "doctor_id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
      "requested_date": "2026-01-31T18:11:28.948589",
      "reason": "Consultation request from Patient 2 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
      "requested_date": "2026-01-31T18:11:28.948589Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "54b20025-30a0-4d6f-b646-5b98b613caee",
      "patient_id": "dc990553-a24f-4838-8d42-5e43790edb74",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:28.962084Z",
      "updated_at": "2026-01-29T18:11:28.962086Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.981893",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "d4ee1792-1496-4782-b773-fef4c51353ca",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:28.997945",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 3 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "d4ee1792-1496-4782-b773-fef4c51353ca",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.016533",
    "method": "POST",
    "endpoint": "/appointments",
    "payload": {
      "doctor_id": "d4ee1792-1496-4782-b773-fef4c51353ca",
      "requested_date": "2026-02-01T18:11:28.997978",
      "reason": "Consultation request from Patient 3 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "d4ee1792-1496-4782-b773-fef4c51353ca",
      "requested_date": "2026-02-01T18:11:28.997978Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "4b98e25b-bd58-4e74-b8ad-7b50c489ff0a",
      "patient_id": "3fec6ac8-92d3-4552-b514-353b2ee20522",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:29.011188Z",
      "updated_at": "2026-01-29T18:11:29.011192Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.031951",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.048274",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 4 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.067597",
    "method": "POST",
    "endpoint": "/appointments",
    "payload": {
      "doctor_id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
      "requested_date": "2026-02-02T18:11:29.048306",
      "reason": "Consultation request from Patient 4 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
      "requested_date": "2026-02-02T18:11:29.048306Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "3f962169-76b4-4d54-8c42-245a7b9c60fb",
      "patient_id": "20e81985-cce8-4af2-afe7-b713e4d8f55e",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:29.062042Z",
      "updated_at": "2026-01-29T18:11:29.062043Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.082296",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.098243",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 5 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:41:29.117170",
    "method": "POST",
    "endpoint": "/appointments",
    "payload": {
      "doctor_id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
      "requested_date": "2026-02-03T18:11:29.098282",
      "reason": "Consultation request from Patient 5 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
      "requested_date": "2026-02-03T18:11:29.098282Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "48999716-5e5b-4ca1-80ee-60a52e47a2b7",
      "patient_id": "64d33677-4106-462b-8580-b3afda1e152b",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:29.111806Z",
      "updated_at": "2026-01-29T18:11:29.111808Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:31.083957",
    "method": "POST",
    "endpoint": "/appointments/36f3a962-0ff6-4c8a-889b-866e6d61a6bb/approve",
    "payload": {
      "appointment_time": "2026-02-03T18:11:29.117268",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "4067f3e0-9301-413d-b300-a3f58e78bf8a",
      "requested_date": "2026-02-03T18:11:29.117268Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "36f3a962-0ff6-4c8a-889b-866e6d61a6bb",
      "patient_id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "98210645726",
      "join_url": "https://zoom.us/j/98210645726?pwd=dLAfNbRXCb5VanfxaCsFeJVDXUwg29.1",
      "start_url": "https://zoom.us/s/98210645726?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5ODIxMDY0NTcyNiIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImY4N2NkZGZmOGU4MDRjZDZiODE1YWVlNDA4MTM4ZDgxIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTc0OTAsImlhdCI6MTc2OTcxMDI5MCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.ARRd9NJzknlO0hPfaXqPQOaKi4L6a3G5jQSs3G0tmEU",
      "meeting_password": "K6iDMA",
      "created_at": "2026-01-29T18:11:28.900266Z",
      "updated_at": "2026-01-29T18:11:31.067470Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:31.103103",
    "method": "PATCH",
    "endpoint": "/appointments/54b20025-30a0-4d6f-b646-5b98b613caee/status",
    "payload": {
      "status": "declined",
      "doctor_notes": "Cannot make it."
    },
    "status": 200,
    "response": {
      "doctor_id": "be0bf68b-aceb-48e0-b5a7-3c9c670b7ea6",
      "requested_date": "2026-01-31T18:11:28.948589Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "54b20025-30a0-4d6f-b646-5b98b613caee",
      "patient_id": "dc990553-a24f-4838-8d42-5e43790edb74",
      "status": "declined",
      "doctor_notes": "Cannot make it.",
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T18:11:28.962084Z",
      "updated_at": "2026-01-29T18:11:31.097253Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:33.162318",
    "method": "POST",
    "endpoint": "/appointments/4b98e25b-bd58-4e74-b8ad-7b50c489ff0a/approve",
    "payload": {
      "appointment_time": "2026-02-03T18:11:31.103153",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "d4ee1792-1496-4782-b773-fef4c51353ca",
      "requested_date": "2026-02-03T18:11:31.103153Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "4b98e25b-bd58-4e74-b8ad-7b50c489ff0a",
      "patient_id": "3fec6ac8-92d3-4552-b514-353b2ee20522",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "99321910325",
      "join_url": "https://zoom.us/j/99321910325?pwd=Vqriih5lhNYmKAeC4ZDo8q7tvH9I0Z.1",
      "start_url": "https://zoom.us/s/99321910325?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5OTMyMTkxMDMyNSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjAwZDQyNmQ0MDNjOTRlOGU4YmY0NjcyNjQ5OTIyOTY1Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTc0OTIsImlhdCI6MTc2OTcxMDI5MiwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.Zg44KrFHFrfHF3f9JKkSrDHGGEayH9czHOvPPun4jCM",
      "meeting_password": "8pd2Tv",
      "created_at": "2026-01-29T18:11:29.011188Z",
      "updated_at": "2026-01-29T18:11:33.149949Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:35.189927",
    "method": "POST",
    "endpoint": "/appointments/3f962169-76b4-4d54-8c42-245a7b9c60fb/approve",
    "payload": {
      "appointment_time": "2026-02-03T18:11:33.162385",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "4f972b37-f685-4b0a-bc5e-e1d30a4c73ac",
      "requested_date": "2026-02-03T18:11:33.162385Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "3f962169-76b4-4d54-8c42-245a7b9c60fb",
      "patient_id": "20e81985-cce8-4af2-afe7-b713e4d8f55e",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "98112500049",
      "join_url": "https://zoom.us/j/98112500049?pwd=btWabbyk1bVa8pfkuOay10lXMbnPaG.1",
      "start_url": "https://zoom.us/s/98112500049?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5ODExMjUwMDA0OSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjJlYzBhYWU1MjU5ZjQ3Yzc5OGI5YTNkZjYyMmIwZDliIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTc0OTQsImlhdCI6MTc2OTcxMDI5NCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.i4aTBFQIuzv9dlbSxnvnI_A_syVDLGkR3golfopV6vA",
      "meeting_password": "0m3y12",
      "created_at": "2026-01-29T18:11:29.062042Z",
      "updated_at": "2026-01-29T18:11:35.180260Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:37.242379",
    "method": "POST",
    "endpoint": "/appointments/48999716-5e5b-4ca1-80ee-60a52e47a2b7/approve",
    "payload": {
      "appointment_time": "2026-02-03T18:11:35.190049",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
      "requested_date": "2026-02-03T18:11:35.190049Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "48999716-5e5b-4ca1-80ee-60a52e47a2b7",
      "patient_id": "64d33677-4106-462b-8580-b3afda1e152b",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "91497007095",
      "join_url": "https://zoom.us/j/91497007095?pwd=zc9PVuBjLcUAG2rGJLbqP9A9vtphLb.1",
      "start_url": "https://zoom.us/s/91497007095?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5MTQ5NzAwNzA5NSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjJkYTkxNjMxZGZlNzQ5YTliMmQ0MDNlZWJiZDU0MjVlIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTc0OTYsImlhdCI6MTc2OTcxMDI5NiwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.zVOz0xlKGzHHqHSulAsk9_XM2SKZoiXa-kSSKlivBn0",
      "meeting_password": "egB0ky",
      "created_at": "2026-01-29T18:11:29.111806Z",
      "updated_at": "2026-01-29T18:11:37.228345Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:37.281756",
    "method": "GET",
    "endpoint": "/doctor/patients/225b710a-f93a-4f70-86d4-66eff97e5c7d/documents",
    "payload": {},
    "status": 200,
    "response": [
      {
        "id": "759a6391-c83e-41dd-9f40-830593630f96",
        "file_name": "CamScanner 1-11-26 13.41.pdf",
        "category": "LAB_REPORT",
        "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
        "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
        "file_size": 7971926,
        "uploaded_at": "2026-01-29T18:11:28.727914Z",
        "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/225b710a-f93a-4f70-86d4-66eff97e5c7d/47fca654-5e85-41f3-8dd5-bb270b703bc0.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T181137Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=375e470440bcb852faa3b34595f2422038bc452883de94af6c459c244a018901"
      }
    ]
  },
  {
    "timestamp": "2026-01-29T23:41:37.356221",
    "method": "POST",
    "endpoint": "/doctor/tasks",
    "payload": {
      "title": "General Ward Round",
      "priority": "normal",
      "due_date": "2026-01-30T18:11:37.281943"
    },
    "status": 201,
    "response": {
      "title": "General Ward Round",
      "description": null,
      "due_date": "2026-01-30T18:11:37.281943Z",
      "priority": "normal",
      "status": "pending",
      "id": "e3b935a6-d0f5-42cf-9a43-c212ca1fa1ab",
      "doctor_id": "7fe5b78a-4d4a-49b2-a8ec-5e8bd04145da",
      "created_at": "2026-01-29T18:11:37.302242Z",
      "updated_at": "2026-01-29T18:11:37.302244Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:41:37.583116",
    "method": "POST",
    "endpoint": "/doctor/ai/process-document",
    "payload": {
      "patient_id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "document_id": "759a6391-c83e-41dd-9f40-830593630f96",
      "processing_type": "comprehensive",
      "priority": "normal"
    },
    "status": 201,
    "response": {
      "job_id": "433e1bdc-115b-4f38-aaad-ec09d3413c59",
      "status": "pending",
      "message": "Document queued for AI processing. Job ID: 433e1bdc-115b-4f38-aaad-ec09d3413c59"
    }
  },
  {
    "timestamp": "2026-01-29T23:46:41.375257",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/patient",
    "payload": {
      "patient_id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "query": "What does my report say about heart rate?",
      "document_id": "759a6391-c83e-41dd-9f40-830593630f96"
    },
    "status": 200,
    "response": "I couldn't find any processed information to answer your question. Please ensure the documents are fully processed."
  },
  {
    "timestamp": "2026-01-29T23:46:43.236649",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/doctor",
    "payload": {
      "patient_id": "225b710a-f93a-4f70-86d4-66eff97e5c7d",
      "query": "Summarize this patient's condition.",
      "document_id": "759a6391-c83e-41dd-9f40-830593630f96"
    },
    "status": 200,
    "response": "I couldn't find any processed information to answer your question. Please ensure the documents are fully processed."
  }
]
```
