"""
Fetch user credentials (emails, ids, role, decrypted full names and patient fields) from the application's database.

Usage examples:
  # Fetch one admin user
  python scripts/generate_credentials.py --role admin --limit 1

  # Fetch all doctors in an organization
  python scripts/generate_credentials.py --role doctor --org-name "Urban City General Hospital"

  # Fetch patients and include patient profile fields
  python scripts/generate_credentials.py --role patient --limit 10

Notes:
- This script reads DB config from app.config.settings and prints stored password hashes (not plaintext passwords).
- PII fields stored encrypted in DB are decrypted before printing.
"""

import argparse
import asyncio
import sys
import os
from typing import List, Dict, Any, Optional

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models.user import User, Organization
from app.models.patient import Patient
from app.core.security import pii_encryption


VALID_ROLES = ("admin", "hospital", "doctor", "patient")


async def fetch_users(role: str, limit: Optional[int], org_name: Optional[str], email_filter: Optional[str]) -> List[Dict[str, Any]]:
    results = []

    async with AsyncSessionLocal() as session:
        # Base query
        stmt = select(User)

        # Join organization if org_name filter provided
        if org_name:
            # find org id first
            org_stmt = select(Organization).where(Organization.name == org_name)
            org_res = await session.execute(org_stmt)
            org = org_res.scalar_one_or_none()
            if not org:
                return []
            stmt = stmt.where(User.organization_id == org.id)

        if role and role != "all":
            stmt = stmt.where(User.role == role)

        if email_filter:
            stmt = stmt.where(User.email == email_filter)

        if limit and isinstance(limit, int):
            stmt = stmt.limit(limit)

        res = await session.execute(stmt)
        users = res.scalars().all()

        for u in users:
            try:
                full_name = pii_encryption.decrypt(u.full_name) if u.full_name else u.full_name
            except Exception:
                # If decryption fails, fall back to raw
                full_name = u.full_name

            item: Dict[str, Any] = {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "password_hash": u.password_hash,
                "full_name": full_name,
                "organization_id": str(u.organization_id) if u.organization_id else None,
            }

            # If patient, fetch patient profile
            if u.role == "patient":
                patient_stmt = select(Patient).where(Patient.id == u.id)
                p_res = await session.execute(patient_stmt)
                p = p_res.scalar_one_or_none()
                if p:
                    try:
                        dob = pii_encryption.decrypt(p.date_of_birth) if p.date_of_birth else p.date_of_birth
                        patient_full_name = pii_encryption.decrypt(p.full_name) if p.full_name else p.full_name
                    except Exception:
                        dob = p.date_of_birth
                        patient_full_name = p.full_name

                    item.update({
                        "patient_mrn": p.mrn,
                        "patient_full_name": patient_full_name,
                        "patient_date_of_birth": dob,
                        "patient_gender": p.gender,
                    })

            results.append(item)

    return results


def print_credentials(creds: List[Dict[str, Any]]):
    if not creds:
        print("No users found matching criteria.")
        return

    for c in creds:
        print("------------------------------")
        print(f"Role:      {c.get('role')}")
        print(f"Email:     {c.get('email')}")
        print(f"ID:        {c.get('id')}")
        print(f"Full name: {c.get('full_name')}")
        print(f"Password hash: {c.get('password_hash')}")
        if c.get("patient_mrn"):
            print(f"MRN:       {c.get('patient_mrn')}")
            print(f"DOB:       {c.get('patient_date_of_birth')}")
            print(f"Gender:    {c.get('patient_gender')}")
    print("------------------------------")


def main():
    parser = argparse.ArgumentParser(description="Fetch credentials for roles from DB")
    parser.add_argument("--role", default="all", help="Role to fetch: admin|hospital|doctor|patient|all")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of users returned")
    parser.add_argument("--org-name", default=None, help="Organization name to filter users by")
    parser.add_argument("--email", default=None, help="Fetch a single user by exact email")

    args = parser.parse_args()

    if args.role != "all" and args.role not in VALID_ROLES:
        print(f"Invalid role: {args.role}. Must be one of: {', '.join(VALID_ROLES)} or 'all'")
        sys.exit(1)

    async def run():
        creds = await fetch_users(args.role, args.limit, args.org_name, args.email)
        print_credentials(creds)

    asyncio.run(run())


if __name__ == "__main__":
    main()
