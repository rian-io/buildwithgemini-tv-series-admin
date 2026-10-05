from google.cloud import firestore

# Project ID explicitly hardcoded as string as required for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-03-3dcdb17c0e1c"
COLLECTION_NAME = "series"

db = firestore.Client(project=PROJECT_ID)

INITIAL_SERIES = [
    {
        "id": "series_001",
        "title": "Cosmic Horizons",
        "genre": ["Sci-Fi", "Adventure"],
        "status": "Airing",
        "seasons": 3,
        "episodes_count": 30,
        "summary": "A team of deep-space explorers discovers a mysterious star gate at the edge of the galaxy.",
        "rating": 8.8,
        "network": "Gemini Streaming"
    },
    {
        "id": "series_002",
        "title": "Cyber Nexus",
        "genre": ["Cyberpunk", "Thriller"],
        "status": "Renewed",
        "seasons": 2,
        "episodes_count": 18,
        "summary": "A rogue ethical hacker uncovers a dark corporate conspiracy in a neon-lit futuristic metropolis.",
        "rating": 8.4,
        "network": "NeoVision"
    },
    {
        "id": "series_003",
        "title": "Chronicles of Eldoria",
        "genre": ["Fantasy", "Drama"],
        "status": "In Production",
        "seasons": 1,
        "episodes_count": 10,
        "summary": "An ancient kingdom faces looming darkness as rival houses compete for the Obsidian Throne.",
        "rating": 9.1,
        "network": "Mythos Original"
    },
    {
        "id": "series_004",
        "title": "Silicon Valley Secrets",
        "genre": ["Drama", "Mystery"],
        "status": "Cancelled",
        "seasons": 1,
        "episodes_count": 8,
        "summary": "An insider whistleblower exposes covert AI experiments inside a massive tech titan.",
        "rating": 7.6,
        "network": "StreamX"
    }
]


def seed_database():
    print(f"Seeding Firestore collection '{COLLECTION_NAME}' in project '{PROJECT_ID}'...")
    collection_ref = db.collection(COLLECTION_NAME)
    for item in INITIAL_SERIES:
        doc_id = item["id"]
        collection_ref.document(doc_id).set(item)
        print(f"  ✓ Added/Updated series: {item['title']} (ID: {doc_id})")
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
