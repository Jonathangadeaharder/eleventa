"""
CQRS (Command Query Responsibility Segregation)

This package implements the CQRS pattern, which separates read operations
(queries) from write operations (commands).

Key Concepts:

1. **Commands** - Represent intent to change state
   - CreateProductCommand, UpdateProductCommand
   - Commands are imperative ("Create", "Update", "Delete")
   - Commands modify state and may fail

2. **Queries** - Represent request for data
   - GetProductByIdQuery, SearchProductsQuery
   - Queries are questions ("Get", "Find", "Search")
   - Queries never modify state, always succeed (or return empty)

3. **Command Handlers** - Process commands
   - Validate business rules
   - Modify domain models
   - Publish domain events
   - Return success/failure

4. **Query Handlers** - Process queries
   - Fetch data from read models
   - Perform joins/aggregations
   - Return DTOs
   - Optimized for reading

5. **Read Models** - Denormalized views
   - Optimized for specific queries
   - Can be cached
   - May be stale (eventual consistency)

Benefits:
- Optimize reads and writes independently
- Scale reads and writes separately
- Simpler query logic (no business rules)
- Better performance
- Clearer intent (command vs query)

References:
- Greg Young's CQRS documents
- Martin Fowler's CQRS article
- Architecture Patterns with Python Chapter 12
"""

from core.cqrs.commands import (
    Command,
    CreateProductCommand,
    UpdateProductCommand,
    DeleteProductCommand,
    ProcessSaleCommand,
)

from core.cqrs.queries import (
    Query,
    GetProductByIdQuery,
    GetProductByCodeQuery,
    SearchProductsQuery,
    GetLowStockProductsQuery,
    GetSalesByDateRangeQuery,
)

from core.cqrs.handlers import (
    CommandHandler,
    QueryHandler,
)

from core.cqrs.read_models import (
    ProductReadModel,
    ProductListItemReadModel,
    SaleReadModel,
    SaleSummaryReadModel,
)

__all__ = [
    # Commands
    "Command",
    "CreateProductCommand",
    "UpdateProductCommand",
    "DeleteProductCommand",
    "ProcessSaleCommand",
    # Queries
    "Query",
    "GetProductByIdQuery",
    "GetProductByCodeQuery",
    "SearchProductsQuery",
    "GetLowStockProductsQuery",
    "GetSalesByDateRangeQuery",
    # Handlers
    "CommandHandler",
    "QueryHandler",
    # Read Models
    "ProductReadModel",
    "ProductListItemReadModel",
    "SaleReadModel",
    "SaleSummaryReadModel",
]
