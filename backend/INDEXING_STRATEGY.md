# Cosmos DB Indexing Strategy

## Overview

Defines indexing policies for Azure Cosmos DB collections to optimize query performance (T172).
Based on data-model.md schema and query patterns from API endpoints.

## Indexing Principles

1. **Partition Key**: Always indexed automatically (`/user_id` or `/id`)
2. **Equality Filters**: Index fields used in WHERE clauses
3. **Range Queries**: Use range indexes for sorting/filtering
4. **Composite Indexes**: For multi-field sorts and filters
5. **Excluded Paths**: Reduce RU cost by excluding large/unused fields

## Collection: users

**Partition Key**: `/id`  
**Query Patterns**:
- Get user by id (login): `id = ?`
- Update preferences: `id = ?`

**Indexing Policy**:
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/password_hash/?"
    },
    {
      "path": "/_etag/?"
    }
  ]
}
```

**Rationale**:
- Simple query pattern (PK lookups only)
- Exclude password_hash (never queried)
- Default indexing sufficient

**Estimated RU Impact**: 10 RU/read, 15 RU/write

---

## Collection: watchlist_items

**Partition Key**: `/user_id`  
**Query Patterns**:
- Get all items: `user_id = ? ORDER BY display_order`
- Check duplicate: `user_id = ? AND symbol = ?`
- Reorder items: `user_id = ? AND display_order IN (?)`

**Indexing Policy**:
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/_etag/?"
    }
  ],
  "compositeIndexes": [
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/display_order",
        "order": "ascending"
      }
    ],
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/symbol",
        "order": "ascending"
      }
    ]
  ]
}
```

**Rationale**:
- **Composite Index 1**: Optimize `ORDER BY display_order` within partition
- **Composite Index 2**: Optimize duplicate symbol check
- `symbol` indexed for equality filters
- `display_order` indexed for range queries and sorting

**Estimated RU Impact**: 
- Get all (sorted): 10 RU
- Check duplicate: 5 RU
- Reorder (update): 15 RU

---

## Collection: portfolio_entries

**Partition Key**: `/user_id`  
**Query Patterns**:
- Get all entries: `user_id = ?`
- Get by category: `user_id = ? AND category = ?`
- Check duplicate: `user_id = ? AND symbol = ? AND category = ?`
- Count entries: `SELECT COUNT(*) WHERE user_id = ?`

**Indexing Policy**:
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/_etag/?"
    }
  ],
  "compositeIndexes": [
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/category",
        "order": "ascending"
      }
    ],
    [
      {
        "path": "/user_id",
        "order": "ascending"
      },
      {
        "path": "/symbol",
        "order": "ascending"
      },
      {
        "path": "/category",
        "order": "ascending"
      }
    ]
  ]
}
```

**Rationale**:
- **Composite Index 1**: Optimize category filtering
- **Composite Index 2**: Optimize duplicate detection (symbol + category)
- All queries are single-partition (efficient)
- `category` has low cardinality (3 values) - highly selective
- `symbol` indexed for duplicate checks

**Estimated RU Impact**: 
- Get all: 10 RU
- Get by category: 8 RU
- Check duplicate: 5 RU
- Count: 5 RU

---

## Collection: stock_quotes (Cache)

**Note**: This is an in-memory cache, not a Cosmos DB collection.  
If implementing persistent cache in Cosmos DB (future optimization):

**Partition Key**: `/symbol`  
**TTL**: 60 seconds  
**Query Patterns**:
- Get quote: `symbol = ?`

**Indexing Policy**:
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/symbol/?"
    }
  ],
  "excludedPaths": [
    {
      "path": "/*"
    }
  ]
}
```

**Rationale**:
- Minimal indexing (only partition key)
- Exclude all other paths (cache data not queried)
- TTL handles expiration automatically

---

## Performance Benefits

### Before Optimization
- Watchlist ORDER BY: Cross-partition sort → 50-100 RU
- Portfolio category filter: Table scan → 100+ RU
- Duplicate checks: Multiple queries → 30+ RU

### After Optimization (T172)
- Watchlist ORDER BY: Composite index → 10 RU (80% reduction)
- Portfolio category filter: Composite index → 8 RU (92% reduction)
- Duplicate checks: Composite index → 5 RU (83% reduction)

**Total Estimated Savings**: 70-85% RU reduction on common queries

---

## Implementation Steps

1. **Development Environment**:
   - Apply indexing policies via Cosmos DB SDK in repository initialization
   - Document in `backend/src/database/indexing_policies.py`

2. **Testing**:
   - Verify composite indexes with query metrics
   - Check RU consumption in Azure Portal

3. **Production**:
   - Apply via Bicep templates (`infrastructure/bicep/cosmos.bicep`)
   - Monitor query performance in Application Insights

4. **Validation**:
   ```bash
   # Check query metrics
   az cosmosdb sql container show \
     --account-name <account> \
     --database-name mystock3 \
     --name portfolio_entries \
     --query 'indexingPolicy'
   ```

---

## Monitoring

**Key Metrics**:
- **Request Charge (RU)**: Should decrease by 70-85% for indexed queries
- **Query Latency**: p95 < 10ms for single-partition queries
- **Index Hit Rate**: Should be >95% for all queries

**Alerts**:
- RU consumption > 100 RU for simple queries
- Cross-partition queries (should never happen with correct partition key)

---

## Notes

- All collections use same partition key strategy (`/user_id`)
- Single-partition queries guaranteed by design
- Composite indexes are order-sensitive (order matters)
- Excluded paths reduce write RU cost by 10-20%
- No wildcard projections in queries to minimize RU cost

**References**:
- [Cosmos DB Indexing Best Practices](https://learn.microsoft.com/azure/cosmos-db/index-policy)
- [Composite Indexes](https://learn.microsoft.com/azure/cosmos-db/index-policy#composite-indexes)
