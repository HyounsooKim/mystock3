#!/usr/bin/env python3
"""Test watchlist update"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.repositories.watchlist_repository import WatchlistRepository
from src.models.watchlist import WatchlistItemUpdate

async def test_update():
    """Test updating memo"""
    repo = WatchlistRepository()
    
    user_id = "user_085bd7ec86dd"
    item_id = "8ee32d8d-c310-4278-865a-adc489d138cc"
    new_memo = "테스트 메모 updated"
    
    print(f"Testing update for user {user_id}, item {item_id}")
    print(f"New memo: {new_memo}")
    
    try:
        # Get existing item
        existing = await repo.get_by_id(user_id, item_id)
        if not existing:
            print(f"❌ Item not found")
            return
        
        print(f"✅ Found existing item: {existing.symbol}, memo: {existing.memo}")
        
        # Update
        updated = await repo.update(user_id, item_id, new_memo, None)
        
        if updated:
            print(f"✅ Update successful")
            print(f"   New memo: {updated.memo}")
        else:
            print(f"❌ Update failed")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_update())
