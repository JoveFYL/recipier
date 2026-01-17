"""
Utility functions for managing seen URLs and crawler state.
"""
import json
import os

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "seen_recipes.json")


def load_seen_urls():
    """Load the set of previously seen URLs from disk."""
    if os.path.exists(DATA_PATH):
        if os.path.getsize(DATA_PATH) == 0:
            return set()
        
        try:
            with open(DATA_PATH, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            print("⚠️  Warning: seen_recipes.json is corrupted, returning empty set")
            return set()
    return set()


def save_seen_urls(seen_set):
    """Save the set of seen URLs to disk."""
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w') as f:
        json.dump(sorted(list(seen_set)), f, indent=2)
    print(f"💾 Saved {len(seen_set)} seen URLs to {DATA_PATH}")


def clear_seen_urls():
    """Clear all seen URLs (useful for starting fresh)."""
    if os.path.exists(DATA_PATH):
        os.remove(DATA_PATH)
        print("🗑️  Cleared all seen URLs")
    else:
        print("ℹ️  No seen URLs file to clear")


def print_seen_stats():
    """Print statistics about seen URLs."""
    seen = load_seen_urls()
    print(f"\n{'='*60}")
    print(f"📊 Seen URLs Statistics")
    print(f"{'='*60}")
    print(f"Total URLs seen: {len(seen)}")
    
    if seen:
        print(f"\nFirst 5 URLs:")
        for url in sorted(list(seen))[:5]:
            print(f"  - {url}")
        
        if len(seen) > 5:
            print(f"  ... and {len(seen) - 5} more")
    else:
        print("No URLs seen yet.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # If run directly, show statistics
    print_seen_stats()
