from app.database import get_client, COLLECTION_NAME, PARENT_COLLECTION_NAME

def wipe_database():
    client = get_client()
    
    print("💥 Nuking old Qdrant collections...")
    
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Deleted Child Collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"⚠️ Skipped {COLLECTION_NAME} (Might not exist): {e}")
        
    try:
        client.delete_collection(collection_name=PARENT_COLLECTION_NAME)
        print(f"✅ Deleted Parent Collection: {PARENT_COLLECTION_NAME}")
    except Exception as e:
        print(f"⚠️ Skipped {PARENT_COLLECTION_NAME} (Might not exist): {e}")

    print("\n🧹 Database is completely clean!")
    print("Restart your FastAPI server. The 'lifespan' function will auto-recreate empty collections.")

if __name__ == "__main__":
    wipe_database()