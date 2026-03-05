"""AWS Service - Handles interactions with AWS Textract, Bedrock, and S3"""

import boto3
import json
import os
import base64
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException

class AWSService:
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not self.access_key or not self.secret_key:
            # warn or just allow init to fail later if not needed immediately
            pass

    def _get_client(self, service_name: str):
        return boto3.client(
            service_name,
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

    async def generate_chat_stream(
        self,
        messages: List[Dict[str, str]],
        context: str,
        system_prompt_override: Optional[str] = None,
    ):
        """
        Streaming generator for chat responses.

        Args:
            messages: Claude-formatted message list [{role, content}]
            context: Medical context text appended to the system prompt
            system_prompt_override: If provided, replaces the default system prompt entirely.
                                    The context is still appended at the end.
        """
        client = self._get_client("bedrock-runtime")

        # Use override if supplied (e.g. guardrail prompt), else generic default
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = "You are a helpful medical assistant. Use the provided context to answer questions accurately."

        if context:
            system_prompt += f"\n\n--- PATIENT MEDICAL CONTEXT ---\n{context}\n--- END OF CONTEXT ---"

        # Format messages for Claude (normalize roles)
        formatted_messages = []
        for m in messages:
            role = "assistant" if m["role"] in ("ai", "assistant") else "user"
            formatted_messages.append({"role": role, "content": m["content"]})
            
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": formatted_messages
        })

        try:
            response = client.invoke_model_with_response_stream(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0", 
                body=body
            )
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_json = json.loads(chunk.get('bytes').decode())
                        if chunk_json.get('type') == 'content_block_delta':
                            yield chunk_json['delta']['text']
        except Exception as e:
            # Fallback: show that context was received even if Bedrock is not configured
            context_preview = context[:300] + "..." if len(context) > 300 else context
            if context and context != "No medical document context available for this patient.":
                yield (
                    f"[MOCK — Bedrock unavailable: {str(e)[:80]}]\n\n"
                    f"Document context WAS retrieved and passed:\n\n{context_preview}\n\n"
                    f"In production with valid AWS credentials, Claude would answer: '{messages[-1]['content']}' "
                    f"using the above context."
                )
            else:
                yield f"[MOCK — Bedrock unavailable] No document context found. Error: {str(e)[:80]}"

    async def extract_text_from_document(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text. Uses PyPDF2 for PDFs if AWS Async is not setup, else Textract for images.
        """
        if file_bytes.startswith(b"%PDF"):
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Mock Textract-like structure
                return {
                    "Blocks": [
                        {"BlockType": "PAGE", "Id": "page-1"},
                        {"BlockType": "LINE", "Text": "PDF Content Extracted Locally", "Id": "line-0"},
                        {"BlockType": "LINE", "Text": text[:1000] + "...", "Id": "line-1"} # Truncate for summary
                    ],
                    "RawText": text
                }
            except ImportError:
                 raise HTTPException(400, "PDF processing requires pypdf library.")
            except Exception as e:
                 raise HTTPException(500, f"PDF Extraction failed: {str(e)}")

        client = self._get_client("textract")
        try:
            response = client.detect_document_text(Document={'Bytes': file_bytes})
            return response
        except Exception as e:
            print(f"Textract Error: {e}")
            raise HTTPException(status_code=500, detail=f"Textract processing failed: {str(e)}")


    async def analyze_image_with_bedrock(self, image_bytes: bytes, prompt: str) -> str:
        """
        Uses Bedrock (Claude 3.5 Sonnet) to analyze an image.
        """
        client = self._get_client("bedrock-runtime")
        
        # Claude 3 message format
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg", # Assuming JPEG for simplicity
                                "data": base64.b64encode(image_bytes).decode('utf-8') if isinstance(image_bytes, bytes) else image_bytes
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        })

        try:
            response = client.invoke_model(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0", 
                body=body
            )
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except ClientError as e:
             raise HTTPException(status_code=500, detail=f"Bedrock analysis failed: {str(e)}")

    async def generate_text(self, prompt: str) -> str:
        """
        Generates text using Bedrock (Claude).
        """
        client = self._get_client("bedrock-runtime")
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        try:
            response = client.invoke_model(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0", 
                body=body
            )
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
        except ClientError as e:
             # Fallback
             print(f"Bedrock generation failed: {e}")
             return "I apologize, but I am unable to generate a response at this time."

    async def generate_soap_note(self, transcript: str, patient_info: Optional[dict] = None) -> dict:
        """
        Generates a structured SOAP note from a doctor-patient consultation transcript
        using AWS Bedrock (Claude 3 Sonnet).

        Args:
            transcript: The full consultation transcript text (speaker-labeled dialogue).
            patient_info: Optional dict with context like name, age, conditions.

        Returns:
            A dict with keys: subjective, objective, assessment, plan.
            Falls back to a mock SOAP note if Bedrock is unavailable.
        """
        client = self._get_client("bedrock-runtime")

        # Build optional patient context block
        patient_context = ""
        if patient_info:
            patient_context = f"\n\nPatient Context:\n{json.dumps(patient_info, indent=2)}\n"

        system_prompt = (
            "You are an expert clinical documentation specialist with deep knowledge of "
            "medical SOAP note formatting. Your task is to convert a doctor-patient "
            "consultation transcript into a structured SOAP note.\n\n"
            "SOAP Note Definitions:\n"
            "- Subjective: Patient's own reported symptoms, history, complaints, and concerns "
            "using their own words. Include onset, duration, severity, and associated symptoms.\n"
            "- Objective: Measurable and observable clinical findings from the encounter, "
            "including vital signs, physical exam findings, and any lab/test results mentioned.\n"
            "- Assessment: Clinical impression, diagnosis, or differential diagnoses "
            "based on the subjective and objective data.\n"
            "- Plan: Treatment plan including medications (with doses), referrals, "
            "follow-up schedule, patient education, and any orders placed.\n\n"
            "RULES:\n"
            "1. Return ONLY a valid JSON object — no markdown, no code fences, no extra text.\n"
            "2. Use complete, professional medical sentences.\n"
            "3. Do not invent information not present in the transcript.\n"
            "4. The JSON must have exactly these four keys: subjective, objective, assessment, plan.\n\n"
            "JSON format:\n"
            '{"subjective": "...", "objective": "...", "assessment": "...", "plan": "..."}'
        )

        user_message = (
            f"Please generate a SOAP note from the following consultation transcript."
            f"{patient_context}\n\n"
            f"TRANSCRIPT:\n{transcript}"
        )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        })

        try:
            response = client.invoke_model(
                modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                body=body
            )
            response_body = json.loads(response.get('body').read())
            raw_text = response_body['content'][0]['text'].strip()

            # Parse the JSON response from Claude
            soap_dict = json.loads(raw_text)

            # Validate all four SOAP keys are present
            required_keys = {"subjective", "objective", "assessment", "plan"}
            if not required_keys.issubset(soap_dict.keys()):
                raise ValueError(f"Missing SOAP keys in response: {soap_dict.keys()}")

            return soap_dict

        except (ClientError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[AWSService] SOAP note generation failed: {e}. Using fallback mock.")
            return self._fallback_soap_note(transcript)

    def _fallback_soap_note(self, transcript: str) -> dict:
        """
        Returns a structured SOAP note mock when Bedrock is unavailable.
        Extracts basic information from the transcript for meaningful fallback.
        """
        # Pull first 3 patient lines as a rough subjective summary
        patient_lines = [
            line.split(":", 1)[1].strip()
            for line in transcript.splitlines()
            if line.lower().startswith("patient")
        ]
        doctor_lines = [
            line.split(":", 1)[1].strip()
            for line in transcript.splitlines()
            if line.lower().startswith("dr.")
        ]

        subjective_summary = " ".join(patient_lines[:3]) if patient_lines else "Patient reported symptoms as noted in transcript."
        plan_summary = doctor_lines[-1] if doctor_lines else "Follow-up and treatment plan as discussed during consultation."

        return {
            "subjective": (
                f"[MOCK — Bedrock unavailable] {subjective_summary}"
            ),
            "objective": (
                "Physical examination and vital signs as documented during the consultation. "
                "Specific findings recorded by the attending physician."
            ),
            "assessment": (
                "Clinical assessment based on patient history, reported symptoms, and physical examination. "
                "Diagnosis to be confirmed with supporting investigations."
            ),
            "plan": (
                f"[MOCK — Bedrock unavailable] {plan_summary}"
            ),
        }

    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generates embeddings using Amazon Titan Text Embeddings.
        """
        client = self._get_client("bedrock-runtime")
        
        body = json.dumps({
            "inputText": text,
        })

        try:
            response = client.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=body
            )
            response_body = json.loads(response.get('body').read())
            return response_body.get('embedding')
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            # Mock embedding for local testing if AWS fails
            import random
            return [random.uniform(-1, 1) for _ in range(1536)] # Titan dimension is 1536

aws_service = AWSService()
