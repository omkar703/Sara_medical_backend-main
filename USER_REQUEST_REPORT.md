# E2E Test Report

Generated: 2026-01-29T17:19:21.206648

## Summary
- Users Created: 10
- Documents Uploaded: 5
- Appointments: 5

## JSON Data Used & API Interactions

```json
[
  {
    "timestamp": "2026-01-29T17:13:44.510319",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor1_1769667223@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 1 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110001",
      "organization_name": "Test Hospital",
      "specialty": "Cardiology",
      "license_number": "LIC-1-1769667223"
    },
    "status": 201,
    "response": {
      "id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
      "name": "Dr. 1 Test",
      "email": "custom_doctor1_1769667223@test.com",
      "first_name": "Dr.",
      "last_name": "1 Test",
      "phone_number": "+15551110001",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T11:43:44.488472Z",
      "updated_at": "2026-01-29T11:43:44.488474Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:44.903634",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor1_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:45.292342",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor2_1769667223@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 2 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110002",
      "organization_name": "Test Hospital",
      "specialty": "Dermatology",
      "license_number": "LIC-2-1769667223"
    },
    "status": 201,
    "response": {
      "id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
      "name": "Dr. 2 Test",
      "email": "custom_doctor2_1769667223@test.com",
      "first_name": "Dr.",
      "last_name": "2 Test",
      "phone_number": "+15551110002",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T11:43:45.280413Z",
      "updated_at": "2026-01-29T11:43:45.280415Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:45.674314",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor2_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:46.091691",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor3_1769667223@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 3 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110003",
      "organization_name": "Test Hospital",
      "specialty": "Pediatrics",
      "license_number": "LIC-3-1769667223"
    },
    "status": 201,
    "response": {
      "id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
      "name": "Dr. 3 Test",
      "email": "custom_doctor3_1769667223@test.com",
      "first_name": "Dr.",
      "last_name": "3 Test",
      "phone_number": "+15551110003",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T11:43:46.072100Z",
      "updated_at": "2026-01-29T11:43:46.072104Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:46.473463",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor3_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:46.860542",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor4_1769667223@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 4 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110004",
      "organization_name": "Test Hospital",
      "specialty": "Neurology",
      "license_number": "LIC-4-1769667223"
    },
    "status": 201,
    "response": {
      "id": "86abac17-8bc3-4404-b421-a825c5b5287d",
      "name": "Dr. 4 Test",
      "email": "custom_doctor4_1769667223@test.com",
      "first_name": "Dr.",
      "last_name": "4 Test",
      "phone_number": "+15551110004",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T11:43:46.848439Z",
      "updated_at": "2026-01-29T11:43:46.848441Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:47.174989",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor4_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:47.417678",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor5_1769667223@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 5 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110005",
      "organization_name": "Test Hospital",
      "specialty": "Orthopedics",
      "license_number": "LIC-5-1769667223"
    },
    "status": 201,
    "response": {
      "id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
      "name": "Dr. 5 Test",
      "email": "custom_doctor5_1769667223@test.com",
      "first_name": "Dr.",
      "last_name": "5 Test",
      "phone_number": "+15551110005",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T11:43:47.404125Z",
      "updated_at": "2026-01-29T11:43:47.404137Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:47.649091",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor5_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:47.893144",
    "method": "POST",
    "endpoint": "/doctor/onboard-patient",
    "payload": {
      "fullName": "Patient 1 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000001",
      "email": "custom_patient1_1769667223@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 200,
    "response": {
      "message": "Patient onboarded successfully",
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "email": "custom_patient1_1769667223@test.com",
      "temporary_password": "SecurePass123!"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:48.124931",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient1_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:48.363597",
    "method": "POST",
    "endpoint": "/doctor/onboard-patient",
    "payload": {
      "fullName": "Patient 2 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000002",
      "email": "custom_patient2_1769667223@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 200,
    "response": {
      "message": "Patient onboarded successfully",
      "patient_id": "ad856d81-283a-4ed7-adb1-0b2367261a09",
      "email": "custom_patient2_1769667223@test.com",
      "temporary_password": "SecurePass123!"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:48.597841",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient2_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:48.832258",
    "method": "POST",
    "endpoint": "/doctor/onboard-patient",
    "payload": {
      "fullName": "Patient 3 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000003",
      "email": "custom_patient3_1769667223@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 200,
    "response": {
      "message": "Patient onboarded successfully",
      "patient_id": "af55e1d7-9472-4cda-abd4-ba2a19858246",
      "email": "custom_patient3_1769667223@test.com",
      "temporary_password": "SecurePass123!"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:49.066883",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient3_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:49.309895",
    "method": "POST",
    "endpoint": "/doctor/onboard-patient",
    "payload": {
      "fullName": "Patient 4 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000004",
      "email": "custom_patient4_1769667223@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 200,
    "response": {
      "message": "Patient onboarded successfully",
      "patient_id": "1a08c527-478b-418c-a699-0f88d13c751d",
      "email": "custom_patient4_1769667223@test.com",
      "temporary_password": "SecurePass123!"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:49.539831",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient4_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:49.794272",
    "method": "POST",
    "endpoint": "/doctor/onboard-patient",
    "payload": {
      "fullName": "Patient 5 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000005",
      "email": "custom_patient5_1769667223@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 200,
    "response": {
      "message": "Patient onboarded successfully",
      "patient_id": "c451c917-277e-4479-aaac-16924d168410",
      "email": "custom_patient5_1769667223@test.com",
      "temporary_password": "SecurePass123!"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.028507",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient5_1769667223@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T17:13:50.230921",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "description": "Test upload of CamScanner 1-11-26 13.41.pdf"
    },
    "status": 201,
    "response": {
      "id": "0a47a064-22d2-469c-a4be-5023c5123d5c",
      "file_name": "CamScanner 1-11-26 13.41.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
      "file_size": 7971926,
      "uploaded_at": "2026-01-29T11:43:50.212205Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/e85909dc-fd87-4f56-a2d1-439ebd47ce5a/7d0cdec4-ecff-4300-829e-2b0cfd219bb2.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114350Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=8d12b2ae9e2e201d74d3adcc6918d375456a2bbb2fbcb7f4d89609796d79798b"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.261766",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "description": "Test upload of K_V_VENKATARAMAN__report.pdf"
    },
    "status": 201,
    "response": {
      "id": "2d57995b-d91e-4baa-a5ff-e8f1d8046ba4",
      "file_name": "K_V_VENKATARAMAN__report.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "notes": "Test upload of K_V_VENKATARAMAN__report.pdf",
      "file_size": 180811,
      "uploaded_at": "2026-01-29T11:43:50.252839Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/ad856d81-283a-4ed7-adb1-0b2367261a09/46ac056a-d8da-4704-94c2-74211d64d27b.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114350Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=a6ffb5f854cf0ec8d5a63b2e3be762d3faea740afe5192443edf84576c3de311"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.288605",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "description": "Test upload of Synthetic_Patient_02_es.pdf"
    },
    "status": 201,
    "response": {
      "id": "c411d0a4-c51e-4c6a-be6e-541d5b8053ed",
      "file_name": "Synthetic_Patient_02_es.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "notes": "Test upload of Synthetic_Patient_02_es.pdf",
      "file_size": 41238,
      "uploaded_at": "2026-01-29T11:43:50.279982Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/af55e1d7-9472-4cda-abd4-ba2a19858246/55a626a1-994d-4c96-85a8-d81df6c0b219.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114350Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=14479049d5db8f80ed782dada9864b4aeb158c9a8f3cd7bbaee8215e95b93298"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.314336",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "description": "Test upload of Synthetic_Patient_04_ar.pdf"
    },
    "status": 201,
    "response": {
      "id": "02f70b5b-0bc9-48ba-9dbd-973af81f1ffa",
      "file_name": "Synthetic_Patient_04_ar.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "notes": "Test upload of Synthetic_Patient_04_ar.pdf",
      "file_size": 61797,
      "uploaded_at": "2026-01-29T11:43:50.304956Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/1a08c527-478b-418c-a699-0f88d13c751d/d34a8c4b-6781-493e-8e50-34d4e938cfdc.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114350Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=5ed43103d806415fef0dbe9d09f503b3aff4427a5c3fb8f3bf7c7d0b2c1633d0"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.341296",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "description": "Test upload of Synthetic_Patient_06_hi-1.pdf"
    },
    "status": 201,
    "response": {
      "id": "da1f18ed-3bf8-445f-8d09-756e1f7478c9",
      "file_name": "Synthetic_Patient_06_hi-1.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "notes": "Test upload of Synthetic_Patient_06_hi-1.pdf",
      "file_size": 54818,
      "uploaded_at": "2026-01-29T11:43:50.331921Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/c451c917-277e-4479-aaac-16924d168410/f14f3e80-db8d-41cb-b617-40cc68d71cd7.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114350Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=3014993216960cbe5ea8251fb61759cae672d2edbe09143fe27ce3b2cb3a9f74"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.359585",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.373834",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 1 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.405598",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
      "requested_date": "2026-01-30T11:43:50.373951",
      "reason": "Consultation request from Patient 1 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
      "requested_date": "2026-01-30T11:43:50.373951Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "1b793443-1f65-4dbe-9071-5bb26f7067be",
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.384392Z",
      "updated_at": "2026-01-29T11:43:50.384393Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.419914",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.434107",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 2 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.450455",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
      "requested_date": "2026-01-31T11:43:50.434142",
      "reason": "Consultation request from Patient 2 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
      "requested_date": "2026-01-31T11:43:50.434142Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "5a80056a-fb2a-40f8-830f-459e65501c7c",
      "patient_id": "ad856d81-283a-4ed7-adb1-0b2367261a09",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.444359Z",
      "updated_at": "2026-01-29T11:43:50.444360Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.465002",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.481155",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 3 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.500772",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
      "requested_date": "2026-02-01T11:43:50.481190",
      "reason": "Consultation request from Patient 3 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
      "requested_date": "2026-02-01T11:43:50.481190Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "8def18b9-b8ce-460a-95cc-7b968e8d68f6",
      "patient_id": "af55e1d7-9472-4cda-abd4-ba2a19858246",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.491062Z",
      "updated_at": "2026-01-29T11:43:50.491063Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.516344",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "86abac17-8bc3-4404-b421-a825c5b5287d",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.531721",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 4 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "86abac17-8bc3-4404-b421-a825c5b5287d",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.551844",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "86abac17-8bc3-4404-b421-a825c5b5287d",
      "requested_date": "2026-02-02T11:43:50.531766",
      "reason": "Consultation request from Patient 4 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "86abac17-8bc3-4404-b421-a825c5b5287d",
      "requested_date": "2026-02-02T11:43:50.531766Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "f73e4a54-6af8-4254-b8a9-7c39fb4624bc",
      "patient_id": "1a08c527-478b-418c-a699-0f88d13c751d",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.542988Z",
      "updated_at": "2026-01-29T11:43:50.542989Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.565271",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.581538",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 5 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T17:13:50.599392",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
      "requested_date": "2026-02-03T11:43:50.581569",
      "reason": "Consultation request from Patient 5 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
      "requested_date": "2026-02-03T11:43:50.581569Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "c6839bf1-c8cd-4985-a410-7c1ed0daf712",
      "patient_id": "c451c917-277e-4479-aaac-16924d168410",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.591828Z",
      "updated_at": "2026-01-29T11:43:50.591831Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:52.694570",
    "method": "POST",
    "endpoint": "/appointments/1b793443-1f65-4dbe-9071-5bb26f7067be/approve",
    "payload": {
      "appointment_time": "2026-02-03T11:43:50.599538",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "59badcd8-c6d7-4880-ae92-82c219a589e4",
      "requested_date": "2026-02-03T11:43:50.599538Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "1b793443-1f65-4dbe-9071-5bb26f7067be",
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "92523402076",
      "join_url": "https://zoom.us/j/92523402076?pwd=4H3e5KF10EQxekXLRNbGLHehSYmBTU.1",
      "start_url": "https://zoom.us/s/92523402076?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5MjUyMzQwMjA3NiIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImU2NDBjMmNjOTk4ZDQ4MDZiNzhmY2U0MGJmMzA3M2ZlIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2OTQyMzIsImlhdCI6MTc2OTY4NzAzMiwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.eVfw_H0OsQ5GBGNUjaMiQzk4d-0OdZeWKwywrknlaOM",
      "meeting_password": "eUCt5X",
      "created_at": "2026-01-29T11:43:50.384392Z",
      "updated_at": "2026-01-29T11:43:52.681336Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:52.715579",
    "method": "PATCH",
    "endpoint": "/appointments/5a80056a-fb2a-40f8-830f-459e65501c7c/status",
    "payload": {
      "status": "declined",
      "doctor_notes": "Cannot make it."
    },
    "status": 200,
    "response": {
      "doctor_id": "f2cb85e8-2999-4138-9eba-935ffc84a006",
      "requested_date": "2026-01-31T11:43:50.434142Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "5a80056a-fb2a-40f8-830f-459e65501c7c",
      "patient_id": "ad856d81-283a-4ed7-adb1-0b2367261a09",
      "status": "declined",
      "doctor_notes": "Cannot make it.",
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T11:43:50.444359Z",
      "updated_at": "2026-01-29T11:43:52.706385Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:53.854487",
    "method": "POST",
    "endpoint": "/appointments/8def18b9-b8ce-460a-95cc-7b968e8d68f6/approve",
    "payload": {
      "appointment_time": "2026-02-03T11:43:52.715647",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "ed9aa3d4-3c79-476e-bcb4-1353ef464a5d",
      "requested_date": "2026-02-03T11:43:52.715647Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "8def18b9-b8ce-460a-95cc-7b968e8d68f6",
      "patient_id": "af55e1d7-9472-4cda-abd4-ba2a19858246",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "94074418865",
      "join_url": "https://zoom.us/j/94074418865?pwd=4dYx0K02VR8um5AtJ6ISNaQ2QAhwLA.1",
      "start_url": "https://zoom.us/s/94074418865?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NDA3NDQxODg2NSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjI0Mzk1ZDJjNjY3ODQ3ZDc4NjA4OTBkOWE1Yzg4MTYwIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2OTQyMzMsImlhdCI6MTc2OTY4NzAzMywiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.83KxkB93hIjfFN1yfymYmZVGkxe03I71HLvq_x6OEJY",
      "meeting_password": "tutz3i",
      "created_at": "2026-01-29T11:43:50.491062Z",
      "updated_at": "2026-01-29T11:43:53.837874Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:55.469868",
    "method": "POST",
    "endpoint": "/appointments/f73e4a54-6af8-4254-b8a9-7c39fb4624bc/approve",
    "payload": {
      "appointment_time": "2026-02-03T11:43:53.854575",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "86abac17-8bc3-4404-b421-a825c5b5287d",
      "requested_date": "2026-02-03T11:43:53.854575Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "f73e4a54-6af8-4254-b8a9-7c39fb4624bc",
      "patient_id": "1a08c527-478b-418c-a699-0f88d13c751d",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "94389047908",
      "join_url": "https://zoom.us/j/94389047908?pwd=cFqbtlauLfio8pevoFZGvJz9ho43lS.1",
      "start_url": "https://zoom.us/s/94389047908?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NDM4OTA0NzkwOCIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjMwNmQ5MmNlMjM2MDQzNDFiNTc5MDg1ZDIyOWIxNDY4Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2OTQyMzUsImlhdCI6MTc2OTY4NzAzNSwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.hx08BsyKI0-SWBBohTdYuaJM-MAieFQaun6K2v4Yuhc",
      "meeting_password": "d58icV",
      "created_at": "2026-01-29T11:43:50.542988Z",
      "updated_at": "2026-01-29T11:43:55.456923Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:57.926844",
    "method": "POST",
    "endpoint": "/appointments/c6839bf1-c8cd-4985-a410-7c1ed0daf712/approve",
    "payload": {
      "appointment_time": "2026-02-03T11:43:55.469924",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
      "requested_date": "2026-02-03T11:43:55.469924Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "c6839bf1-c8cd-4985-a410-7c1ed0daf712",
      "patient_id": "c451c917-277e-4479-aaac-16924d168410",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "94291748160",
      "join_url": "https://zoom.us/j/94291748160?pwd=GELSq66Ibgf24rOFwqItqAbJ0noZ8N.1",
      "start_url": "https://zoom.us/s/94291748160?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NDI5MTc0ODE2MCIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjA0ZTkwM2MxYmI5NDQxOWNiYjUzNjA3OWYyYjUwMDYwIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk2OTQyMzcsImlhdCI6MTc2OTY4NzAzNywiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.ik0vxG68N4C3tl-kL80x0cGF_VaakSeAM9_isfdUD0k",
      "meeting_password": "xC1jQY",
      "created_at": "2026-01-29T11:43:50.591828Z",
      "updated_at": "2026-01-29T11:43:57.913406Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:57.963485",
    "method": "GET",
    "endpoint": "/doctor/patients/e85909dc-fd87-4f56-a2d1-439ebd47ce5a/documents",
    "payload": {},
    "status": 200,
    "response": [
      {
        "id": "0a47a064-22d2-469c-a4be-5023c5123d5c",
        "file_name": "CamScanner 1-11-26 13.41.pdf",
        "category": "LAB_REPORT",
        "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
        "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
        "file_size": 7971926,
        "uploaded_at": "2026-01-29T11:43:50.212205Z",
        "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/e85909dc-fd87-4f56-a2d1-439ebd47ce5a/7d0cdec4-ecff-4300-829e-2b0cfd219bb2.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T114357Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=4d9219f9a948011c6559e97be0b21f779df86a7af6d4a6e6f73aaa1008292ed5"
      }
    ]
  },
  {
    "timestamp": "2026-01-29T17:13:57.998947",
    "method": "POST",
    "endpoint": "/doctor/tasks",
    "payload": {
      "title": "General Ward Round",
      "priority": "normal",
      "due_date": "2026-01-30T11:43:57.963616"
    },
    "status": 201,
    "response": {
      "title": "General Ward Round",
      "description": null,
      "due_date": "2026-01-30T11:43:57.963616Z",
      "priority": "normal",
      "status": "pending",
      "id": "2058b8b0-b67b-4b53-ba23-7ffcb77c0015",
      "doctor_id": "d184f0b0-ce83-4528-aa23-13a7b6b78bf8",
      "created_at": "2026-01-29T11:43:57.981825Z",
      "updated_at": "2026-01-29T11:43:57.981828Z"
    }
  },
  {
    "timestamp": "2026-01-29T17:13:58.251898",
    "method": "POST",
    "endpoint": "/doctor/ai/process-document",
    "payload": {
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "document_id": "0a47a064-22d2-469c-a4be-5023c5123d5c",
      "processing_type": "comprehensive",
      "priority": "normal"
    },
    "status": 201,
    "response": {
      "job_id": "969a4214-db69-4a18-86de-5577b9bee18f",
      "status": "pending",
      "message": "Document queued for AI processing. Job ID: 969a4214-db69-4a18-86de-5577b9bee18f"
    }
  },
  {
    "timestamp": "2026-01-29T17:19:06.971682",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/patient",
    "payload": {
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "query": "What does my report say about heart rate?",
      "document_id": "0a47a064-22d2-469c-a4be-5023c5123d5c"
    },
    "status": 200,
    "response": "Unfortunately, none of the medical reports and test results provided in the context mention anything about heart rate or heart-related findings. The reports cover blood tests, imaging scans like chest X-ray and PET CT, as well as laboratory analyses of proteins and immunoglobulins, but I could not find any specific information regarding the patient's heart rate.\n\nAs an AI assistant without direct access to the patient's full medical records, I cannot provide any professional medical advice. My response is based solely on the limited context provided. For any specific medical concerns or interpretation of test results, it's crucial to consult with a licensed healthcare professional who can review the complete medical history and provide appropriate guidance tailored to the individual's condition."
  },
  {
    "timestamp": "2026-01-29T17:19:21.206559",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/doctor",
    "payload": {
      "patient_id": "e85909dc-fd87-4f56-a2d1-439ebd47ce5a",
      "query": "Summarize this patient's condition.",
      "document_id": "0a47a064-22d2-469c-a4be-5023c5123d5c"
    },
    "status": 200,
    "response": "Based on the context provided from the medical records, the patient Mr. K V VENKATARAMAN seems to be suffering from multiple myeloma, which is a type of plasma cell neoplasm or cancer of the plasma cells in the blood. The key findings that support this condition are:\n\n1. Bone marrow aspiration and biopsy showing morphological features indicative of plasma cell neoplasm, with increased plasma cells accounting for 35% of total nucleated cells in the aspirate and 60-65% cellularity in the trephine biopsy.\n\n2. Pathological fractures in multiple vertebrae (T7, T12, and L4) are mentioned, which can be associated with multiple myeloma.\n\n3. Blood tests show abnormal levels of proteins and immunoglobulins like elevated B-2 microglobulin, abnormal immunoglobulin levels (IgG, IgM, IgA), and the presence of paraproteins.\n\n4. Imaging findings like osteogenic skeletal changes and hypermetabolism in the PET-CT scan are suggestive of malignant bone involvement.\n\nAdditionally, the patient seems to have complications like a Klebsiella pneumoniae infection (based on positive sputum culture), pulmonary edema (vascular cuffing on chest X-ray), and renal involvement (increased creatinine levels, nephrologist consultation).\n\nHowever, please note that I am an AI assistant and this should not be considered professional medical advice. It is always recommended to consult with a qualified healthcare professional for accurate diagnosis and appropriate treatment."
  }
]
```
