#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import defaultdict
import hashlib

# Add project root to Python path so we can import our modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database import get_chromadb_client
from scraper.utils import save_seen_urls


def cleanup_duplicates():
    """
    Main function to clean up duplicates and populate seen_recipes.json.
    """
    
    # Step 1: Connect to ChromaDB
    client = get_chromadb_client()
    collection = client.get_or_create_collection(name="recipes")
    
    # Step 2: Get total count first (efficient way to check collection size)
    total_chunks = collection.count()
    
    if total_chunks == 0:
        print("Collection is empty. Nothing to clean up.")
        return
    
    # Step 3: Retrieve ALL documents with metadata in batches
    all_ids = []
    all_documents = []
    all_metadatas = []

    batch_size = 300
    offset = 0
    
    while True:
        batch = collection.get(
            limit=batch_size,  # Get all remaining items
            include=['documents', 'metadatas'],
            offset=offset
        )
        
        if not batch['ids']:
            break
            
        all_ids.extend(batch['ids'])
        all_documents.extend(batch['documents'])
        all_metadatas.extend(batch['metadatas'])
        
        offset += batch_size
        
        if len(batch['ids']) < batch_size:
          break
    
    print(f"Retrieved {len(all_ids)} chunks successfully")
    
    # Step 4: Identify duplicates by content hash
    print(f"\nAnalyzing content to identify duplicates...")
    
    # Dictionary to track unique content
    # Key: content_hash (unique identifier for the content)
    # Value: list of IDs that share this content
    content_map = defaultdict(list)
    
    # Track dishes for seen_recipes.json
    dishes = set()
    
    # Iterate through each chunk
    for i, doc_id in enumerate(all_ids):
        document = all_documents[i]
        metadata = all_metadatas[i]
        
        # Extract key information from metadata
        recipe_name = metadata.get('recipe', 'Unknown')
        chunk_type = metadata.get('type', 'unknown')
        
        # If chunk is a title and the dish is not in the set, add it to the set
        if metadata['type'] == 'title' and metadata['recipe'] not in dishes:
            dishes.add(metadata['recipe'])
        
        # Create a unique and deterministic hash for this content
        # Format: "recipe_name:chunk_type:actual_content"
        # identify exact duplicates
        content_string = f"{recipe_name}:{chunk_type}:{document}"
        
        # encode text to bytes and hash using md5 and change to hexadecimal string
        content_hash = hashlib.md5(content_string.encode()).hexdigest()
        
        # Add this ID to the list of IDs with this content
        content_map[content_hash].append(doc_id)
    
    # Step 5: Determine which IDs are duplicates
    duplicate_ids = []
    unique_content_count = 0
    
    for content_hash, id_list in content_map.items():
        unique_content_count += 1
        
        if len(id_list) > 1:
            # identified duplicate
            # Keep the FIRST occurrence, mark the REST as duplicates to delete
            duplicates_for_this_content = id_list[1:]  # Skip the first one
            duplicate_ids.extend(duplicates_for_this_content)
            
            # Show user what we found
            print(f"  Found {len(id_list)} copies of same content " 
                  f"(keeping 1, removing {len(id_list)-1})")
    
    # Step 6: Display analysis results
    print(f"\n" + "=" * 70)
    print(f"ANALYSIS RESULTS:")
    print(f"=" * 70)
    print(f"  Total chunks in database:    {total_chunks}")
    print(f"  Unique content pieces:       {unique_content_count}")
    print(f"  Duplicate chunks to remove:  {len(duplicate_ids)}")
    print(f"  Database size reduction:     {len(duplicate_ids) / total_chunks * 100:.1f}%")
    print(f"  Dishes seen found:           {len(dishes)}")
    print("=" * 70)
    
    # Step 7: Check if there are any duplicates to remove
    if len(duplicate_ids) == 0:
        print("\nNo duplicates found.")
        
        # Still dishes seen to seen_recipes.json
        if dishes:
            print(f"\nSaving {len(dishes)} seen dishes to seen_recipes.json...")
            save_seen_urls(dishes)
        
        return
    
    # Step 8: Get user confirmation before deleting
    print(f"\nWARNING: This will permanently DELETE {len(duplicate_ids)} duplicate chunks.")
    response = input("Do you want to proceed? Type 'yes' to continue: ").strip().lower()
    
    if response != 'yes':
        print("\nOperation cancelled. No changes were made.")
        return
    
    # Step 9: Delete duplicates in batches (respecting 300-item limit)
    print(f"\nDeleting {len(duplicate_ids)} duplicate chunks...")
    print("   (Processing in batches of 300 due to ChromaDB limits)")
    
    # ChromaDB has a limit of ~300 items per delete operation
    DELETE_BATCH_SIZE = 300
    total_batches = (len(duplicate_ids) + DELETE_BATCH_SIZE - 1) // DELETE_BATCH_SIZE
    
    deleted_count = 0
    
    # Process deletions in batches
    for batch_num in range(total_batches):
        # Calculate batch start and end indices
        start_idx = batch_num * DELETE_BATCH_SIZE
        end_idx = min(start_idx + DELETE_BATCH_SIZE, len(duplicate_ids))
        
        # Extract this batch of IDs to delete
        batch_ids = duplicate_ids[start_idx:end_idx]
        
        # Delete this batch from ChromaDB
        collection.delete(ids=batch_ids)
        
        deleted_count += len(batch_ids)
        
        # Show progress
        print(f"   ✓ Batch {batch_num + 1}/{total_batches}: "
              f"Deleted {len(batch_ids)} items "
              f"(Total: {deleted_count}/{len(duplicate_ids)})")
    
    # Step 10: Verify the cleanup worked
    final_count = collection.count()
    removed_count = total_chunks - final_count
    
    print(f"\n" + "=" * 70)
    print(f"CLEANUP COMPLETE!")
    print(f"=" * 70)
    print(f"  Chunks before:  {total_chunks}")
    print(f"  Chunks after:   {final_count}")
    print(f"  Chunks removed: {removed_count}")
    print(f"  Success rate:   {removed_count / len(duplicate_ids) * 100:.1f}%")
    print("=" * 70)
    
    # Step 11: Save seen dishes to seen_recipes.json
    if dishes:
        print(f"\nSaving {len(dishes)} source seen dishes to seen_recipes.json...")
        save_seen_urls(dishes)
        print(f"Seen dishes saved successfully!")
    else:
        print(f"\nNo source seen dishes found in metadata.")
        print(f"   Tip: Update your scraper to include 'title' in metadata")
    
    print(f"\nAll done! Your database is now clean and deduplicated.")


if __name__ == "__main__":
    try:
        cleanup_duplicates()
    except KeyboardInterrupt:
        print("\n\n  Operation interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
