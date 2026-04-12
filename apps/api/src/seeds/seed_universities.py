"""
Seed script for universities.
Run with: python -m src.seeds.seed_universities
"""
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import SessionLocal, engine
from src.models import *  # noqa
from src.database import Base
from src.models.university import University, UniversityPolicyEntry


def seed():
    Base.metadata.create_all(bind=engine)

    seed_file = os.path.join(os.path.dirname(__file__), "universities.json")
    with open(seed_file) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        seeded = 0
        for uni_data in data:
            existing = db.query(University).filter(University.slug == uni_data["slug"]).first()
            if existing:
                print(f"  Skipping {uni_data['slug']} (already exists)")
                continue

            policy_entries = uni_data.pop("policy_entries", [])
            university = University(**uni_data)
            db.add(university)
            db.flush()

            for entry_data in policy_entries:
                entry = UniversityPolicyEntry(
                    university_id=university.id,
                    **entry_data,
                )
                db.add(entry)

            db.commit()
            seeded += 1
            print(f"  Seeded: {university.name} ({len(policy_entries)} policy entries)")

        print(f"\nDone. {seeded} universities seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding universities...")
    seed()
