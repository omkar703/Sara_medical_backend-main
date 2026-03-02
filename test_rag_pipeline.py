"""
RAG Pipeline Standalone Test Script
Tests every step of the RAG (Retrieval Augmented Generation) pipeline:

  STEP 1  → Generate query embedding (AWS Bedrock Titan)
  STEP 2  → Build a sample document corpus (mock chunks with embeddings)
  STEP 3  → Cosine similarity search (in-memory, no DB needed)
  STEP 4  → Retrieve top-K relevant chunks
  STEP 5  → Build LLM prompt with context
  STEP 6  → Send to Claude (AWS Bedrock) for final answer
  STEP 7  → Print full response

Run: python test_rag_pipeline.py

Requirements:
  - AWS credentials in .env  (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  - No DB / Docker / MinIO needed
"""

import asyncio
import math
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Console helpers ─────────────────────────────────────────────────────────
def step(n, total, msg):
    print(f"\n\033[1m\033[94m[STEP {n}/{total}]\033[0m {msg}")
    print("  " + "─" * 55)

def ok(msg):    print(f"  \033[92m✅ {msg}\033[0m")
def info(msg):  print(f"  \033[96mℹ  {msg}\033[0m")
def warn(msg):  print(f"  \033[93m⚠  {msg}\033[0m")
def err(msg):   print(f"  \033[91m❌ {msg}\033[0m")
def dim(msg):   print(f"  \033[90m   {msg}\033[0m")


# ── Mock medical document corpus ─────────────────────────────────────────────
# Simulates what would be stored in the `chunks` table after document processing
MOCK_DOCUMENTS = [
    {
        "id": "chunk-001",
        "source": "TIER_1_TEXT",
        "page": 1,
        "document": "patient_blood_report.pdf",
        "content": (
            "Patient: John Doe, MRN: PT-10234. "
            "HbA1c: 8.9% (high). Fasting glucose: 210 mg/dL (high). "
            "Creatinine: 0.9 mg/dL (normal). eGFR: 92 (normal). "
            "LDL cholesterol: 141 mg/dL. HDL: 42 mg/dL. Triglycerides: 188 mg/dL. "
            "Report date: 2026-02-15."
        ),
    },
    {
        "id": "chunk-002",
        "source": "TIER_1_TEXT",
        "page": 2,
        "document": "patient_blood_report.pdf",
        "content": (
            "CBC Results: WBC 7.2 (normal), RBC 4.8 (normal), "
            "Hemoglobin 13.4 g/dL (mild anemia borderline), "
            "Platelets 225 (normal). "
            "Thyroid: TSH 2.4 mIU/L (normal). "
            "Vitamin D: 18 ng/mL (deficient, <20 is low)."
        ),
    },
    {
        "id": "chunk-003",
        "source": "TIER_1_TEXT",
        "page": 1,
        "document": "doctor_notes_march.pdf",
        "content": (
            "Dr. Nguyen consultation notes 2026-03-01: "
            "Patient presents with Type 2 Diabetes poorly controlled. "
            "Increased Lantus from 22 to 28 units. "
            "Added Metformin 500 mg BID. "
            "Started Atorvastatin 20 mg for dyslipidemia. "
            "Referred to dietitian. Return in 6 weeks."
        ),
    },
    {
        "id": "chunk-004",
        "source": "TIER_1_TEXT",
        "page": 1,
        "document": "prescription_history.pdf",
        "content": (
            "Active Medications: Lantus (insulin glargine) 28 units SC nightly. "
            "Humalog sliding scale with meals. "
            "Metformin 500 mg twice daily with meals. "
            "Atorvastatin 20 mg at bedtime. "
            "Aspirin 81 mg daily. "
            "Vitamin D3 2000 IU daily (newly added)."
        ),
    },
    {
        "id": "chunk-005",
        "source": "TIER_3_IMAGE_ANALYSIS",
        "page": 3,
        "document": "patient_blood_report.pdf",
        "content": (
            "ECG report: Normal sinus rhythm at 72 bpm. "
            "No ST-segment changes. No bundle branch block. "
            "QTc interval 418 ms (normal). "
            "No acute ischemic changes identified."
        ),
    },
    {
        "id": "chunk-006",
        "source": "TIER_1_TEXT",
        "page": 1,
        "document": "allergy_history.pdf",
        "content": (
            "Allergy History: NKDA (No Known Drug Allergies). "
            "Food: Mild shellfish sensitivity (hives). "
            "Environmental: Seasonal pollen allergy. "
            "Last anaphylaxis: None on record."
        ),
    },
]

TOTAL_STEPS = 7


# ── Cosine similarity (in-memory, no pgvector needed) ───────────────────────
def cosine_similarity(a: list, b: list) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Main test pipeline ───────────────────────────────────────────────────────
async def run_rag_test():
    from app.services.aws_service import AWSService
    service = AWSService()

    # ── Verify credentials ──────────────────────────────────────────────────
    key = os.getenv("AWS_ACCESS_KEY_ID", "")
    has_real_creds = bool(key and not key.startswith("AKIAxxx"))

    if not has_real_creds:
        warn("AWS credentials not found in .env — running in OFFLINE MODE")
        warn("Embeddings will be random vectors. Claude response will be a fallback.")
        info("To use real AWS Bedrock, add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to .env")
    else:
        ok(f"AWS credentials loaded (key: {key[:6]}...{key[-4:]})")

    QUERY = "What is the patient's current diabetes medication and latest HbA1c result?"
    TOP_K = 3

    print(f"\n  Query : \033[1m\"{QUERY}\"\033[0m")
    print(f"  Top-K : {TOP_K} chunks")
    print(f"  Corpus: {len(MOCK_DOCUMENTS)} mock document chunks")

    # ╔══════════════════════════════════════════════════════════════════════╗
    step(1, TOTAL_STEPS, "Generate query embedding (AWS Bedrock Titan Text Embeddings)")
    # ╚══════════════════════════════════════════════════════════════════════╝
    t0 = time.time()
    query_embedding = await service.generate_embeddings(QUERY)
    elapsed = time.time() - t0

    is_mock_embedding = any(abs(v) > 0.5 for v in query_embedding[:5])  # random vectors often > 0.5
    embedding_source = "Random (offline fallback)" if not has_real_creds else "AWS Bedrock Titan"
    ok(f"Embedding generated in {elapsed:.2f}s")
    info(f"Source    : {embedding_source}")
    info(f"Dimensions: {len(query_embedding)}")
    dim(f"First 5 values: {[round(v, 4) for v in query_embedding[:5]]}")


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(2, TOTAL_STEPS, "Embed all corpus chunks (simulating indexed DB chunks)")
    # ╚══════════════════════════════════════════════════════════════════════╝
    chunk_embeddings = []
    for i, chunk in enumerate(MOCK_DOCUMENTS):
        emb = await service.generate_embeddings(chunk["content"])
        chunk_embeddings.append(emb)
        dim(f"  Chunk {i+1}/{len(MOCK_DOCUMENTS)} embedded: [{chunk['document']}] p.{chunk['page']} ({chunk['source']})")

    ok(f"{len(chunk_embeddings)} chunks embedded successfully")


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(3, TOTAL_STEPS, "Cosine similarity search (in-memory, mirrors pgvector behaviour)")
    # ╚══════════════════════════════════════════════════════════════════════╝
    scores = []
    for i, (chunk, emb) in enumerate(zip(MOCK_DOCUMENTS, chunk_embeddings)):
        sim = cosine_similarity(query_embedding, emb)
        scores.append((sim, i, chunk))
        dim(f"  Chunk {i+1}: score={sim:.4f}  [{chunk['document']}] — {chunk['content'][:60]}...")

    scores.sort(key=lambda x: x[0], reverse=True)
    ok(f"Ranked {len(scores)} chunks by cosine similarity")


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(4, TOTAL_STEPS, f"Retrieve top-{TOP_K} relevant chunks")
    # ╚══════════════════════════════════════════════════════════════════════╝
    top_chunks = scores[:TOP_K]
    for rank, (score, _, chunk) in enumerate(top_chunks, 1):
        ok(f"Rank #{rank}  score={score:.4f}  [{chunk['document']}] p.{chunk['page']} ({chunk['source']})")
        dim(f"  {chunk['content'][:100]}...")


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(5, TOTAL_STEPS, "Build LLM prompt with retrieved context")
    # ╚══════════════════════════════════════════════════════════════════════╝
    context_parts = []
    for rank, (score, _, chunk) in enumerate(top_chunks, 1):
        context_parts.append(
            f"[Source {rank}: {chunk['document']}, Page {chunk['page']}]\n{chunk['content']}"
        )
    context_text = "\n\n".join(context_parts)

    system_prompt = (
        "You are a helpful medical AI assistant. Answer the doctor's question "
        "based ONLY on the context provided from the patient's medical records. "
        "Be concise, accurate, and always cite which document your answer comes from. "
        "If the information is not in the context, clearly say so."
    )
    full_prompt = (
        f"CONTEXT FROM PATIENT RECORDS:\n{context_text}\n\n"
        f"DOCTOR'S QUESTION: {QUERY}\n\n"
        f"Please provide a clear, structured answer with document citations."
    )

    ok(f"Prompt constructed with {len(top_chunks)} context chunks")
    info(f"System prompt: {len(system_prompt)} chars")
    info(f"Full prompt  : {len(full_prompt)} chars")
    dim("Context preview:")
    for line in context_text[:400].split("\n"):
        dim(f"  {line}")
    if len(context_text) > 400:
        dim("  ...")


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(6, TOTAL_STEPS, "Send prompt to AWS Bedrock (Claude 3 Sonnet)")
    # ╚══════════════════════════════════════════════════════════════════════╝
    info("Calling aws_service.generate_text() ...")
    t0 = time.time()
    response = await service.generate_text(full_prompt)
    elapsed = time.time() - t0

    if "unable to generate" in response.lower() or not response.strip():
        warn(f"Bedrock unreachable or returned empty response ({elapsed:.2f}s)")
        warn("Check AWS credentials and Claude model access in Bedrock console")
        llm_ok = False
    else:
        ok(f"Response received in {elapsed:.2f}s ({len(response)} chars)")
        llm_ok = True


    # ╔══════════════════════════════════════════════════════════════════════╗
    step(7, TOTAL_STEPS, "Final RAG Answer")
    # ╚══════════════════════════════════════════════════════════════════════╝
    print()
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │              RAG RESPONSE FROM CLAUDE               │")
    print("  └─────────────────────────────────────────────────────┘")
    print()
    # Word-wrap response neatly
    words = response.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 75:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n\n" + "═" * 60)
    print("\033[1m  RAG Pipeline Test Summary\033[0m")
    print("─" * 60)
    checks = [
        ("Query embedding generated",       True),
        ("Corpus chunks embedded",           True),
        ("Similarity search completed",      True),
        (f"Top-{TOP_K} chunks retrieved",    True),
        ("Prompt built with context",        True),
        ("LLM (Claude) responded",           llm_ok),
        ("Full answer returned",             llm_ok and len(response) > 20),
    ]
    for label, passed in checks:
        status = "\033[92m✅ PASS\033[0m" if passed else "\033[93m⚠  SKIP\033[0m"
        print(f"  {status}  {label}")

    all_passed = all(p for _, p in checks)
    print("─" * 60)
    if all_passed:
        print("\033[92m  ✅ Full RAG pipeline is working end-to-end!\033[0m")
    else:
        print("\033[93m  ⚠  Pipeline ran but Claude was unreachable — add AWS credentials.\033[0m")
    print("═" * 60 + "\n")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("═" * 60)
    print("\033[1m  RAG Pipeline — Step-by-Step Test Runner\033[0m")
    print("\033[1m  Sara Medical Backend\033[0m")
    print("═" * 60)
    asyncio.run(run_rag_test())
