import sys
from pathlib import Path
import shutil
# Remove pytest dependency
# import pytest 

# Add src to path if needed (though PYTHONPATH should handle it)
# sys.path.append('src')

from bookmarkcli.store import BookmarkStore
from bookmarkcli.models import Bookmark

def test_comma_in_tag_bug(tmp_path):
    db_path = tmp_path / "db.sqlite"
    store = BookmarkStore(db_path)
    store.initialize()
    
    # Create a bookmark
    bm = store.create(url="http://example.com")
    print(f"Created bookmark {bm.id}")
    
    # Try to add a tag with a comma
    tag = "foo,bar"
    print(f"Adding tag: '{tag}'")
    
    try:
        updated = store.add_tag(bm.id, tag)
        print(f"Updated tags immediately returned: {updated.tags}")
    except Exception as e:
        print(f"Error adding tag: {e}")
        return

    # Fetch it back from DB to be sure
    bm_loaded = store.get(bm.id)
    print(f"Loaded tags from DB: {bm_loaded.tags}")
    
    # Bug check:
    # If bug exists, "foo,bar" is split into "foo" and "bar"
    if "foo" in bm_loaded.tags and "bar" in bm_loaded.tags:
        print("BUG CONFIRMED: 'foo,bar' was split into 'foo' and 'bar'")
        
        # Now try to remove it
        print("Attempting to remove 'foo,bar'...")
        try:
            store.remove_tag(bm.id, tag)
            print("Removed successfully (Unexpected!)")
        except Exception as e:
            print(f"Failed to remove: {e}")
            print("CONFIRMED: Cannot remove tag 'foo,bar' after adding it.")

        raise AssertionError("Bug Confirmed")
    elif "foo,bar" in bm_loaded.tags:
        print("NO BUG: 'foo,bar' was preserved as a single tag")
    else:
        print(f"Unexpected state: {bm_loaded.tags}")

if __name__ == "__main__":
    try:
        tmp = Path("./tmp_test_bug")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()
        test_comma_in_tag_bug(tmp)
        # cleanup
        # shutil.rmtree(tmp)
    except AssertionError:
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
