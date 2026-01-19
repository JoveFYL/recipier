#!/usr/bin/env python3
"""
Quick script to check for duplicates without deleting anything.
Safe to run - this is read-only.
"""
import sys
from pathlib import Path
from collections import Counter, defaultdict
import hashlib

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database import get_chromadb_client


def check_duplicates():
    """Check for duplicates in the collection (read-only)."""
    
    print("🔍 Checking for duplicates (read-only, no changes will be made)...\n")
    
    # Connect to ChromaDB
    client = get_chromadb_client()
    collection = client.get_or_create_collection(name="recipes")
    
    # Get all data
    all_data = collection.get(
        limit=None,
        include=['documents', 'metadatas']
    )
    
    total_chunks = len(all_data['ids'])
    print(f"📊 Total chunks in database: {total_chunks}\n")
    
    if total_chunks == 0:
        print("⚠️  Database is empty!")
        return
    
    # Count recipes
    recipe_counts = Counter(
        metadata.get('recipe', 'Unknown')
        for metadata in all_data['metadatas']
    )
    
    print(f"🍳 Unique recipes: {len(recipe_counts)}")
    print(f"📦 Average chunks per recipe: {total_chunks / len(recipe_counts):.1f}\n")
    
    # Find content duplicates
    content_map = defaultdict(list)
    source_urls = set()
    
    for i, doc_id in enumerate(all_data['ids']):
        document = all_data['documents'][i]
        metadata = all_data['metadatas'][i]
        
        # Track URLs
        if 'source_url' in metadata:
            source_urls.add(metadata['source_url'])
        
        # Hash content
        recipe_name = metadata.get('recipe', 'Unknown')
        chunk_type = metadata.get('type', 'unknown')
        content_hash = hashlib.md5(
            f"{recipe_name}:{chunk_type}:{document}".encode()
        ).hexdigest()
        
        content_map[content_hash].append(doc_id)
    
    # Count duplicates
    unique_content = len(content_map)
    duplicate_count = sum(len(ids) - 1 for ids in content_map.values() if len(ids) > 1)
    
    print(f"🔎 Duplicate Analysis:")
    print(f"  Unique content pieces:  {unique_content}")
    print(f"  Duplicate copies:       {duplicate_count}")
    print(f"  Duplication rate:       {duplicate_count / total_chunks * 100:.1f}%\n")
    
    print(f"🔗 Source URLs found in metadata: {len(source_urls)}")
    
    if duplicate_count > 0:
        print(f"\n💡 Run 'python3 cleanup_duplicates.py' to remove {duplicate_count} duplicates")
    else:
        print(f"\n✅ No duplicates found! Database is clean.")
    
    # Show top recipes by chunk count
    print(f"\n📋 Top 10 recipes by chunk count:")
    for recipe, count in recipe_counts.most_common(10):
        print(f"  {count:3d} chunks - {recipe}")


if __name__ == "__main__":
    check_duplicates()
