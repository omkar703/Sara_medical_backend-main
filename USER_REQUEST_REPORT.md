# E2E Test Report

Generated: 2026-01-29T23:17:43.030464

## Summary
- Users Created: 10
- Documents Uploaded: 5
- Appointments: 5

## JSON Data Used & API Interactions

```json
[
  {
    "timestamp": "2026-01-29T23:12:17.598290",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor1_1769688736@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 1 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110001",
      "organization_name": "Test Hospital",
      "specialty": "Cardiology",
      "license_number": "LIC-1-1769688736"
    },
    "status": 201,
    "response": {
      "id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
      "name": "Dr. 1 Test",
      "email": "custom_doctor1_1769688736@test.com",
      "first_name": "Dr.",
      "last_name": "1 Test",
      "phone_number": "+15551110001",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T17:42:17.581453Z",
      "updated_at": "2026-01-29T17:42:17.581455Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:17.984531",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor1_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:18.366855",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor2_1769688736@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 2 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110002",
      "organization_name": "Test Hospital",
      "specialty": "Dermatology",
      "license_number": "LIC-2-1769688736"
    },
    "status": 201,
    "response": {
      "id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
      "name": "Dr. 2 Test",
      "email": "custom_doctor2_1769688736@test.com",
      "first_name": "Dr.",
      "last_name": "2 Test",
      "phone_number": "+15551110002",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T17:42:18.357964Z",
      "updated_at": "2026-01-29T17:42:18.357966Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:18.749400",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor2_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:19.132612",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor3_1769688736@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 3 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110003",
      "organization_name": "Test Hospital",
      "specialty": "Pediatrics",
      "license_number": "LIC-3-1769688736"
    },
    "status": 201,
    "response": {
      "id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
      "name": "Dr. 3 Test",
      "email": "custom_doctor3_1769688736@test.com",
      "first_name": "Dr.",
      "last_name": "3 Test",
      "phone_number": "+15551110003",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T17:42:19.121010Z",
      "updated_at": "2026-01-29T17:42:19.121011Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:19.514910",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor3_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:19.897817",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor4_1769688736@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 4 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110004",
      "organization_name": "Test Hospital",
      "specialty": "Neurology",
      "license_number": "LIC-4-1769688736"
    },
    "status": 201,
    "response": {
      "id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
      "name": "Dr. 4 Test",
      "email": "custom_doctor4_1769688736@test.com",
      "first_name": "Dr.",
      "last_name": "4 Test",
      "phone_number": "+15551110004",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T17:42:19.890556Z",
      "updated_at": "2026-01-29T17:42:19.890558Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:20.284992",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor4_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:20.551868",
    "method": "POST",
    "endpoint": "/auth/register",
    "payload": {
      "email": "custom_doctor5_1769688736@test.com",
      "password": "SecurePass123!",
      "full_name": "Dr. 5 Test",
      "role": "doctor",
      "date_of_birth": "1975-01-01",
      "phone_number": "+15551110005",
      "organization_name": "Test Hospital",
      "specialty": "Orthopedics",
      "license_number": "LIC-5-1769688736"
    },
    "status": 201,
    "response": {
      "id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
      "name": "Dr. 5 Test",
      "email": "custom_doctor5_1769688736@test.com",
      "first_name": "Dr.",
      "last_name": "5 Test",
      "phone_number": "+15551110005",
      "role": "doctor",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "mfa_enabled": false,
      "email_verified": true,
      "created_at": "2026-01-29T17:42:20.546674Z",
      "updated_at": "2026-01-29T17:42:20.546676Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:20.778198",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_doctor5_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:21.039579",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 1 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000001",
      "email": "custom_patient1_1769688736@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 1 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000001",
      "email": "custom_patient1_1769688736@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "mrn": "ORG-2026-000106-2918",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T17:42:20.787395",
      "updated_at": "2026-01-29T17:42:20.787395"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:21.269888",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient1_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:21.505184",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 2 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000002",
      "email": "custom_patient2_1769688736@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 2 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000002",
      "email": "custom_patient2_1769688736@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "0229ef6f-1c32-4edc-ba18-78d53c4dd2d4",
      "mrn": "ORG-2026-000107-3327",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T17:42:21.278421",
      "updated_at": "2026-01-29T17:42:21.278421"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:21.744048",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient2_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:21.974213",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 3 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000003",
      "email": "custom_patient3_1769688736@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 3 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000003",
      "email": "custom_patient3_1769688736@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "4b583512-0962-4430-a484-0d70307a4e98",
      "mrn": "ORG-2026-000108-4443",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T17:42:21.752586",
      "updated_at": "2026-01-29T17:42:21.752586"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:22.200788",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient3_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:22.435002",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 4 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000004",
      "email": "custom_patient4_1769688736@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 4 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000004",
      "email": "custom_patient4_1769688736@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "4d198085-1209-46b5-9a39-ceb0a8e67525",
      "mrn": "ORG-2026-000109-8898",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T17:42:22.209384",
      "updated_at": "2026-01-29T17:42:22.209384"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:22.685549",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient4_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:22.919735",
    "method": "POST",
    "endpoint": "/patients",
    "payload": {
      "fullName": "Patient 5 Test",
      "dateOfBirth": "1980-01-01",
      "phoneNumber": "+15550000005",
      "email": "custom_patient5_1769688736@test.com",
      "password": "SecurePass123!",
      "gender": "male"
    },
    "status": 201,
    "response": {
      "fullName": "Patient 5 Test",
      "dateOfBirth": "1980-01-01",
      "gender": "male",
      "phoneNumber": "+15550000005",
      "email": "custom_patient5_1769688736@test.com",
      "address": null,
      "emergencyContact": null,
      "medicalHistory": null,
      "allergies": [],
      "medications": [],
      "id": "abfe41f0-19d7-4a11-8aa3-7e46389b48ad",
      "mrn": "ORG-2026-000110-0690",
      "organization_id": "97d20f27-b550-4aae-b976-44e8b6f277b6",
      "created_at": "2026-01-29T17:42:22.694702",
      "updated_at": "2026-01-29T17:42:22.694702"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.146643",
    "method": "POST",
    "endpoint": "/auth/login",
    "payload": {
      "email": "custom_patient5_1769688736@test.com",
      "password": "SecurePass123!"
    },
    "status": 200,
    "response": "HIDDEN_TOKEN_RESPONSE"
  },
  {
    "timestamp": "2026-01-29T23:12:23.389464",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "description": "Test upload of CamScanner 1-11-26 13.41.pdf"
    },
    "status": 201,
    "response": {
      "id": "526ffa52-d56f-4401-8860-8d3bea08961a",
      "file_name": "CamScanner 1-11-26 13.41.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
      "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
      "file_size": 7971926,
      "uploaded_at": "2026-01-29T17:42:23.373008Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99/c1659160-c5bb-41fa-821a-f4902ab7d120.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174223Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=9bfb46218aa52740fafb4ff1f660f8a1338c9d9ae749d528e24c4c195483181b"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.417898",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "description": "Test upload of K_V_VENKATARAMAN__report.pdf"
    },
    "status": 201,
    "response": {
      "id": "b276ab53-b11c-497d-b90d-cd31ff4f8aa6",
      "file_name": "K_V_VENKATARAMAN__report.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: K_V_VENKATARAMAN__report.pdf",
      "notes": "Test upload of K_V_VENKATARAMAN__report.pdf",
      "file_size": 180811,
      "uploaded_at": "2026-01-29T17:42:23.410824Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/0229ef6f-1c32-4edc-ba18-78d53c4dd2d4/e7ce51ce-a242-412e-8d4f-2195bb71696a.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174223Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=c28dc20900b917133da4d6747548bbbbe487c6d5ecc82a3a6700caf9a991a938"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.440891",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "description": "Test upload of Synthetic_Patient_02_es.pdf"
    },
    "status": 201,
    "response": {
      "id": "94f2f983-91e4-4c0e-9a4c-823f248c8479",
      "file_name": "Synthetic_Patient_02_es.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_02_es.pdf",
      "notes": "Test upload of Synthetic_Patient_02_es.pdf",
      "file_size": 41238,
      "uploaded_at": "2026-01-29T17:42:23.434579Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/4b583512-0962-4430-a484-0d70307a4e98/dbba3ac0-3a42-473d-9b9a-209cd23ba194.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174223Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=0c59d0d10a917c913118880f3f5ee23c0c2d72cd2b37d9935b6ed99e22f40121"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.464363",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "description": "Test upload of Synthetic_Patient_04_ar.pdf"
    },
    "status": 201,
    "response": {
      "id": "0b3bb30b-420f-42e0-b956-35728d8cd3b0",
      "file_name": "Synthetic_Patient_04_ar.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_04_ar.pdf",
      "notes": "Test upload of Synthetic_Patient_04_ar.pdf",
      "file_size": 61797,
      "uploaded_at": "2026-01-29T17:42:23.457544Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/4d198085-1209-46b5-9a39-ceb0a8e67525/20ab89c0-0b74-4a32-9545-15b4837295e0.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174223Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=ba17e40c398ae87064b2175c5391e87f2a29cdd1229b05e52dd04deb653b71d9"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.487050",
    "method": "POST",
    "endpoint": "/patient/medical-history",
    "payload": {
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "description": "Test upload of Synthetic_Patient_06_hi-1.pdf"
    },
    "status": 201,
    "response": {
      "id": "fd28bd75-aac7-4cd1-9aa6-d465bc4940b2",
      "file_name": "Synthetic_Patient_06_hi-1.pdf",
      "category": "LAB_REPORT",
      "title": "Uploaded: Synthetic_Patient_06_hi-1.pdf",
      "notes": "Test upload of Synthetic_Patient_06_hi-1.pdf",
      "file_size": 54818,
      "uploaded_at": "2026-01-29T17:42:23.480873Z",
      "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/abfe41f0-19d7-4a11-8aa3-7e46389b48ad/2210c6ad-b2a2-4972-8e2d-a3bac4d3b91a.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174223Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=1056990deafd2eab0bb4126dcdd3f2e15d3fbf07f7cefddeba9810dca33af043"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.500644",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.512275",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 1 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
          "name": "Dr. 1 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.538313",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
      "requested_date": "2026-01-30T17:42:23.512343",
      "reason": "Consultation request from Patient 1 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
      "requested_date": "2026-01-30T17:42:23.512343Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "eb110966-9b8b-4d9c-8a25-d8578e161296",
      "patient_id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.522221Z",
      "updated_at": "2026-01-29T17:42:23.522222Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.550311",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.561620",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 2 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
          "name": "Dr. 2 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.576207",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
      "requested_date": "2026-01-31T17:42:23.561648",
      "reason": "Consultation request from Patient 2 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
      "requested_date": "2026-01-31T17:42:23.561648Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "8b6c2b04-b247-4296-b09a-62a8b6e50e1e",
      "patient_id": "0229ef6f-1c32-4edc-ba18-78d53c4dd2d4",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.570608Z",
      "updated_at": "2026-01-29T17:42:23.570609Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.587730",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.602184",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 3 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
          "name": "Dr. 3 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.616911",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
      "requested_date": "2026-02-01T17:42:23.602217",
      "reason": "Consultation request from Patient 3 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
      "requested_date": "2026-02-01T17:42:23.602217Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "df14db8d-31a1-4d76-8d35-d00c866ffbd6",
      "patient_id": "4b583512-0962-4430-a484-0d70307a4e98",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.611603Z",
      "updated_at": "2026-01-29T17:42:23.611604Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.629026",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.642588",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 4 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
          "name": "Dr. 4 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.657942",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
      "requested_date": "2026-02-02T17:42:23.642619",
      "reason": "Consultation request from Patient 4 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
      "requested_date": "2026-02-02T17:42:23.642619Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "2e339a37-23d9-4ac5-9c5e-92e233671a5b",
      "patient_id": "4d198085-1209-46b5-9a39-ceb0a8e67525",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.652076Z",
      "updated_at": "2026-01-29T17:42:23.652077Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.669933",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {},
    "status": 200,
    "response": {
      "results": [
        {
          "id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.682046",
    "method": "GET",
    "endpoint": "/doctors/search",
    "payload": {
      "query": "Dr. 5 Test"
    },
    "status": 200,
    "response": {
      "results": [
        {
          "id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
          "name": "Dr. 5 Test",
          "specialty": null,
          "photo_url": null
        }
      ]
    }
  },
  {
    "timestamp": "2026-01-29T23:12:23.697115",
    "method": "POST",
    "endpoint": "/appointments/request",
    "payload": {
      "doctor_id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
      "requested_date": "2026-02-03T17:42:23.682077",
      "reason": "Consultation request from Patient 5 Test",
      "grant_access_to_history": true
    },
    "status": 201,
    "response": {
      "doctor_id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
      "requested_date": "2026-02-03T17:42:23.682077Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "e989df1e-4574-4df0-bde3-104881875d82",
      "patient_id": "abfe41f0-19d7-4a11-8aa3-7e46389b48ad",
      "status": "pending",
      "doctor_notes": null,
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.691367Z",
      "updated_at": "2026-01-29T17:42:23.691368Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:28.238934",
    "method": "POST",
    "endpoint": "/appointments/eb110966-9b8b-4d9c-8a25-d8578e161296/approve",
    "payload": {
      "appointment_time": "2026-02-03T17:42:23.697227",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "e1878586-4dbc-41ed-a967-37ec035d0f7a",
      "requested_date": "2026-02-03T17:42:23.697227Z",
      "reason": "Consultation request from Patient 1 Test",
      "id": "eb110966-9b8b-4d9c-8a25-d8578e161296",
      "patient_id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "92284688452",
      "join_url": "https://zoom.us/j/92284688452?pwd=OdnsDlqJPpPmKk6ler0O2xHATbJf6r.1",
      "start_url": "https://zoom.us/s/92284688452?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5MjI4NDY4ODQ1MiIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6IjIyNjM0Yjc5M2MyMDQzZDc5ODA4NzRmNjZkODBiYjlhIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTU3NDcsImlhdCI6MTc2OTcwODU0NywiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.kveU9P4t67r0B3-Ugmsog6gignyoWpYwlePQ-hz8yPI",
      "meeting_password": "Ey8p81",
      "created_at": "2026-01-29T17:42:23.522221Z",
      "updated_at": "2026-01-29T17:42:28.211570Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:28.264014",
    "method": "PATCH",
    "endpoint": "/appointments/8b6c2b04-b247-4296-b09a-62a8b6e50e1e/status",
    "payload": {
      "status": "declined",
      "doctor_notes": "Cannot make it."
    },
    "status": 200,
    "response": {
      "doctor_id": "30bfbdc1-186d-4d9f-9f75-60919537fd93",
      "requested_date": "2026-01-31T17:42:23.561648Z",
      "reason": "Consultation request from Patient 2 Test",
      "id": "8b6c2b04-b247-4296-b09a-62a8b6e50e1e",
      "patient_id": "0229ef6f-1c32-4edc-ba18-78d53c4dd2d4",
      "status": "declined",
      "doctor_notes": "Cannot make it.",
      "meeting_id": null,
      "join_url": null,
      "start_url": null,
      "meeting_password": null,
      "created_at": "2026-01-29T17:42:23.570608Z",
      "updated_at": "2026-01-29T17:42:28.255309Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:30.422788",
    "method": "POST",
    "endpoint": "/appointments/df14db8d-31a1-4d76-8d35-d00c866ffbd6/approve",
    "payload": {
      "appointment_time": "2026-02-03T17:42:28.264098",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "bb48d453-e92a-4cc3-945c-f1ac3ba62b00",
      "requested_date": "2026-02-03T17:42:28.264098Z",
      "reason": "Consultation request from Patient 3 Test",
      "id": "df14db8d-31a1-4d76-8d35-d00c866ffbd6",
      "patient_id": "4b583512-0962-4430-a484-0d70307a4e98",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "96425972881",
      "join_url": "https://zoom.us/j/96425972881?pwd=exw68586JmIGQuW5BsHmizWzQN7TWS.1",
      "start_url": "https://zoom.us/s/96425972881?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NjQyNTk3Mjg4MSIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImQ5MmFjYTA0MzM1YjQxN2Q5YmYwMGViYWU3NmJkOTg4Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTU3NTAsImlhdCI6MTc2OTcwODU1MCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.PiTG5N9VM9qehJCVDtDZfh9To7j4YrVWrmgrFN3cA6U",
      "meeting_password": "86Bguh",
      "created_at": "2026-01-29T17:42:23.611603Z",
      "updated_at": "2026-01-29T17:42:30.405739Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:32.410105",
    "method": "POST",
    "endpoint": "/appointments/2e339a37-23d9-4ac5-9c5e-92e233671a5b/approve",
    "payload": {
      "appointment_time": "2026-02-03T17:42:30.422891",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "3e8740cd-d519-48a8-841d-40bc31b7f19e",
      "requested_date": "2026-02-03T17:42:30.422891Z",
      "reason": "Consultation request from Patient 4 Test",
      "id": "2e339a37-23d9-4ac5-9c5e-92e233671a5b",
      "patient_id": "4d198085-1209-46b5-9a39-ceb0a8e67525",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "96627524264",
      "join_url": "https://zoom.us/j/96627524264?pwd=rPzDnGsdVhrYvMAvHgIk4uZV4wRSBj.1",
      "start_url": "https://zoom.us/s/96627524264?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NjYyNzUyNDI2NCIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImEyMTE2MmIzZDc4ODRhMmRhZmY3NjlhYjZmNTI1ZTU1Iiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTU3NTIsImlhdCI6MTc2OTcwODU1MiwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9.foW9gxT20RNMgCn5H2DT1bAfI1ujB-Sz4bHE-M9LpVw",
      "meeting_password": "4CPJ9R",
      "created_at": "2026-01-29T17:42:23.652076Z",
      "updated_at": "2026-01-29T17:42:32.400971Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:34.427622",
    "method": "POST",
    "endpoint": "/appointments/e989df1e-4574-4df0-bde3-104881875d82/approve",
    "payload": {
      "appointment_time": "2026-02-03T17:42:32.410217",
      "doctor_notes": "See you then."
    },
    "status": 200,
    "response": {
      "doctor_id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
      "requested_date": "2026-02-03T17:42:32.410217Z",
      "reason": "Consultation request from Patient 5 Test",
      "id": "e989df1e-4574-4df0-bde3-104881875d82",
      "patient_id": "abfe41f0-19d7-4a11-8aa3-7e46389b48ad",
      "status": "accepted",
      "doctor_notes": "See you then.",
      "meeting_id": "96428916122",
      "join_url": "https://zoom.us/j/96428916122?pwd=u9g4fxVUb9vlgKrQ6ZWbH7M28MQ6g9.1",
      "start_url": "https://zoom.us/s/96428916122?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMiIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJpc3MiOiJ3ZWIiLCJjbHQiOjAsIm1udW0iOiI5NjQyODkxNjEyMiIsImF1ZCI6ImNsaWVudHNtIiwidWlkIjoiSW1RZXF3NGlSejJ1d2V5NlFTaDlWdyIsInppZCI6ImExNzk0NGNiYzYyYjQxODg5YmFlNjRmMTEwZmUyMDZlIiwic2siOiIwIiwic3R5IjoxLCJ3Y2QiOiJhdzEiLCJleHAiOjE3Njk3MTU3NTQsImlhdCI6MTc2OTcwODU1NCwiYWlkIjoiWkp0ZE5CRTBSckNZSjRXQjJzeFRsdyIsImNpZCI6IiJ9._hgINeVUtdyKOL210pXT3gs3P6BuZ7_lyuN0C0SFYqg",
      "meeting_password": "85t19w",
      "created_at": "2026-01-29T17:42:23.691367Z",
      "updated_at": "2026-01-29T17:42:34.405779Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:34.458110",
    "method": "GET",
    "endpoint": "/doctor/patients/ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99/documents",
    "payload": {},
    "status": 200,
    "response": [
      {
        "id": "526ffa52-d56f-4401-8860-8d3bea08961a",
        "file_name": "CamScanner 1-11-26 13.41.pdf",
        "category": "LAB_REPORT",
        "title": "Uploaded: CamScanner 1-11-26 13.41.pdf",
        "notes": "Test upload of CamScanner 1-11-26 13.41.pdf",
        "file_size": 7971926,
        "uploaded_at": "2026-01-29T17:42:23.373008Z",
        "presigned_url": "http://minio:9000/saramedico-medical-records/medical-records/97d20f27-b550-4aae-b976-44e8b6f277b6/ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99/c1659160-c5bb-41fa-821a-f4902ab7d120.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=saramedico_minio_admin%2F20260129%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260129T174234Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=d8d193975a30a3066153ce50218f36f5db7f1009ef51534d2141da80fdc4de06"
      }
    ]
  },
  {
    "timestamp": "2026-01-29T23:12:34.527184",
    "method": "POST",
    "endpoint": "/doctor/tasks",
    "payload": {
      "title": "General Ward Round",
      "priority": "normal",
      "due_date": "2026-01-30T17:42:34.458257"
    },
    "status": 201,
    "response": {
      "title": "General Ward Round",
      "description": null,
      "due_date": "2026-01-30T17:42:34.458257Z",
      "priority": "normal",
      "status": "pending",
      "id": "fb03b457-905d-432e-aaa6-3acf0457513b",
      "doctor_id": "cd968529-fe6f-433c-a3a9-056ff0a8a6cb",
      "created_at": "2026-01-29T17:42:34.481705Z",
      "updated_at": "2026-01-29T17:42:34.481708Z"
    }
  },
  {
    "timestamp": "2026-01-29T23:12:34.829678",
    "method": "POST",
    "endpoint": "/doctor/ai/process-document",
    "payload": {
      "patient_id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "document_id": "526ffa52-d56f-4401-8860-8d3bea08961a",
      "processing_type": "comprehensive",
      "priority": "normal"
    },
    "status": 201,
    "response": {
      "job_id": "068b0cb2-c629-47b5-9ddd-1fffcf20c031",
      "status": "pending",
      "message": "Document queued for AI processing. Job ID: 068b0cb2-c629-47b5-9ddd-1fffcf20c031"
    }
  },
  {
    "timestamp": "2026-01-29T23:17:39.054670",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/patient",
    "payload": {
      "patient_id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "query": "What does my report say about heart rate?",
      "document_id": "526ffa52-d56f-4401-8860-8d3bea08961a"
    },
    "status": 200,
    "response": "I couldn't find any processed information to answer your question. Please ensure the documents are fully processed."
  },
  {
    "timestamp": "2026-01-29T23:17:43.029866",
    "method": "POST",
    "endpoint": "/doctor/ai/chat/doctor",
    "payload": {
      "patient_id": "ee7d5a6f-0eed-4867-9f81-1b03ba9b8d99",
      "query": "Summarize this patient's condition.",
      "document_id": "526ffa52-d56f-4401-8860-8d3bea08961a"
    },
    "status": 200,
    "response": "I couldn't find any processed information to answer your question. Please ensure the documents are fully processed."
  }
]
```
