## CQRS (Command Query Responsibility Segregation) Guide

## Table of Contents

1. [Overview](#overview)
2. [What is CQRS?](#what-is-cqrs)
3. [Commands vs Queries](#commands-vs-queries)
4. [Read Models](#read-models)
5. [Implementation](#implementation)
6. [Usage Examples](#usage-examples)
7. [Performance Optimizations](#performance-optimizations)
8. [Event Integration](#event-integration)
9. [Testing](#testing)
10. [Best Practices](#best-practices)

---

## Overview

CQRS is an architectural pattern that separates **read operations** (queries) from **write operations** (commands). This is **Phase 3** of our architectural improvements.

### What Was Added

- **Commands**: Write operations (CreateProduct, UpdateProduct, ProcessSale)
- **Queries**: Read operations (GetProductById, SearchProducts, GetSalesReport)
- **Command Handlers**: Process commands, validate, publish events
- **Query Handlers**: Fetch data from read models
- **Read Models**: Denormalized views optimized for queries
- **Query Repositories**: Specialized repositories for fast reads

---

## What is CQRS?

### Traditional Approach (No CQRS)

```
┌─────────────┐
│     UI      │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Service    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Repository  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Database   │  Same model for reads and writes
└─────────────┘
```

**Problems:**
- Complex queries join multiple tables (slow)
- Read and write models conflict (normalized for writes, denormalized for reads)
- Hard to optimize (can't cache writes, can't scale reads independently)
- Business logic mixed with query logic

### CQRS Approach

```
Write Side (Commands)              Read Side (Queries)
┌─────────────┐                   ┌─────────────┐
│   Command   │                   │    Query    │
└──────┬──────┘                   └──────┬──────┘
       │                                  │
       ↓                                  ↓
┌─────────────┐                   ┌─────────────┐
│  Command    │                   │   Query     │
│  Handler    │                   │  Handler    │
└──────┬──────┘                   └──────┬──────┘
       │                                  │
       ↓                                  ↓
┌─────────────┐                   ┌─────────────┐
│   Domain    │───Events───>      │    Read     │
│   Model     │                   │   Models    │
└──────┬──────┘                   └──────┬──────┘
       │                                  │
       ↓                                  ↓
┌─────────────┐                   ┌─────────────┐
│Write Database│                  │ Read Database│
│ (Normalized)│                   │(Denormalized)│
└─────────────┘                   └─────────────┘
```

**Benefits:**
- ✅ Optimize reads and writes independently
- ✅ Scale reads and writes separately
- ✅ Simpler query logic (no business rules)
- ✅ Better performance (denormalized reads, caching)
- ✅ Clear separation of concerns

---

## Commands vs Queries

### Commands (Write Operations)

Commands represent **intent to change state**. They are **imperative** and **may fail**.

**Characteristics:**
- Named as imperatives: `CreateProduct`, `UpdatePrice`, `ProcessSale`
- Can fail (validation errors, business rule violations)
- Modify state
- Publish domain events
- Transactional
- Return success/failure

**Example:**
```python
# Command
command = CreateProductCommand(
    code="LAPTOP001",
    description="Dell Laptop",
    sell_price=Decimal('999.99'),
    user_id=current_user_id
)

# Handle command
result = command_handler.handle(command)

if result.is_success:
    product_id = result.data  # UUID of created product
else:
    print(f"Failed: {result.error}")
    if result.errors:
        for field, error in result.errors.items():
            print(f"  {field}: {error}")
```

### Queries (Read Operations)

Queries represent **requests for data**. They are **questions** and **never modify state**.

**Characteristics:**
- Named as questions: `GetProduct`, `FindCustomers`, `SearchSales`
- Never fail (return None or empty list)
- Never modify state
- Can be cached aggressively
- Return read models (not domain models)
- Can use denormalized data
- Can return stale data (eventual consistency)

**Example:**
```python
# Query
query = SearchProductsQuery(
    search_term="laptop",
    in_stock_only=True,
    limit=20
)

# Handle query
products = query_handler.handle(query)  # List[ProductListItemReadModel]

# Always succeeds (empty list if no results)
for product in products:
    print(f"{product.code}: ${product.sell_price}")
```

### Key Differences

| Aspect | Commands | Queries |
|--------|----------|---------|
| Purpose | Change state | Fetch data |
| Naming | Imperative (Create, Update) | Question (Get, Find) |
| Can fail? | Yes | No (return None/empty) |
| Modify state? | Yes | No |
| Transactional? | Yes | No |
| Can be cached? | No | Yes |
| Return | Success/Failure | Data or None |
| Model | Domain Model | Read Model |

---

## Read Models

Read models are **denormalized views** optimized for specific queries.

### ProductReadModel (Complete View)

```python
@dataclass(frozen=True)
class ProductReadModel:
    """Complete product view with denormalized data."""
    id: UUID
    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal]
    quantity_in_stock: Decimal

    # Denormalized from related tables
    department_id: Optional[UUID]
    department_name: Optional[str]  # ← Denormalized!
    unit_id: Optional[UUID]
    unit_name: Optional[str]  # ← Denormalized!

    # Computed fields
    in_stock: bool  # ← Pre-calculated
    is_low_stock: bool  # ← Pre-calculated
    stock_value: Decimal  # ← Pre-calculated
```

**Without CQRS** (Traditional):
```sql
-- Every query needs JOINs
SELECT p.*, d.name, u.name,
       (p.quantity > 0) as in_stock,
       (p.quantity < p.min) as is_low_stock,
       (p.quantity * p.cost) as stock_value
FROM products p
LEFT JOIN departments d ON p.department_id = d.id
LEFT JOIN units u ON p.unit_id = u.id
WHERE p.id = ?
```

**With CQRS** (Read Model):
```sql
-- Single table, no JOINs!
SELECT * FROM product_read_view WHERE id = ?

-- Or even better, from cache:
cache.get("product:{id}")
```

### ProductListItemReadModel (List View)

```python
@dataclass(frozen=True)
class ProductListItemReadModel:
    """Lightweight product for lists."""
    id: UUID
    code: str
    description: str
    sell_price: Decimal
    quantity_in_stock: Decimal
    department_name: Optional[str]  # Denormalized
    in_stock: bool
    is_low_stock: bool

    # No cost_price, no unit, no timestamps
    # Only what's needed for list display
```

### DashboardSummaryReadModel (Aggregated View)

```python
@dataclass(frozen=True)
class DashboardSummaryReadModel:
    """Pre-aggregated dashboard data."""
    # Today's metrics (pre-calculated)
    today_sales_total: Decimal
    today_sales_count: int
    today_avg_sale: Decimal

    # This week
    week_sales_total: Decimal
    week_sales_count: int

    # Inventory
    low_stock_product_count: int
    total_inventory_value: Decimal

    # Recent sales (pre-fetched)
    recent_sales: List[SaleSummaryReadModel]

    # This entire model could be cached for 5 minutes!
```

---

## Implementation

### 1. Define Commands

```python
# core/cqrs/commands.py

@dataclass(frozen=True)
class CreateProductCommand(Command):
    """Command to create a new product."""
    code: str
    description: str
    sell_price: Decimal
    cost_price: Optional[Decimal] = None
    department_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
```

### 2. Create Command Handler

```python
# core/cqrs/handlers.py

class CreateProductCommandHandler(CommandHandler[CreateProductCommand, UUID]):
    """Handles product creation."""

    def __init__(self, product_service: ProductService):
        super().__init__()
        self.product_service = product_service

    def handle(self, command: CreateProductCommand) -> UseCaseResult[UUID]:
        # 1. Validate
        errors = self._validate(command)
        if errors:
            return UseCaseResult.validation_error(errors)

        # 2. Execute business logic
        try:
            product = self.product_service.add_product(...)

            # 3. Events published automatically by UnitOfWork

            return UseCaseResult.success(product.id)
        except ValueError as e:
            return UseCaseResult.failure(str(e))
```

### 3. Define Queries

```python
# core/cqrs/queries.py

@dataclass(frozen=True)
class SearchProductsQuery(Query):
    """Query to search products."""
    search_term: Optional[str] = None
    department_id: Optional[UUID] = None
    in_stock_only: bool = False
    limit: int = 100
```

### 4. Create Query Handler

```python
# core/cqrs/handlers.py

class SearchProductsQueryHandler(QueryHandler[SearchProductsQuery, List[ProductListItemReadModel]]):
    """Handles product search."""

    def __init__(self, query_repository: ProductQueryRepository):
        super().__init__()
        self.query_repository = query_repository

    def handle(self, query: SearchProductsQuery) -> List[ProductListItemReadModel]:
        # No validation needed - queries never fail
        # Fetch from optimized read model
        return self.query_repository.search_products(
            search_term=query.search_term,
            department_id=query.department_id,
            in_stock_only=query.in_stock_only,
            limit=query.limit
        )
```

### 5. Update Read Models via Events

```python
# core/event_handlers.py

@EventPublisher.subscribe(ProductCreated)
def update_product_read_model(event: ProductCreated):
    """Update denormalized product view when product is created."""

    # Option 1: Insert into denormalized table
    execute_sql("""
        INSERT INTO product_read_view (
            id, code, description, sell_price,
            department_name, in_stock, stock_value
        )
        SELECT
            p.id, p.code, p.description, p.sell_price,
            d.name, (p.quantity > 0), (p.quantity * p.cost)
        FROM products p
        LEFT JOIN departments d ON p.department_id = d.id
        WHERE p.id = :product_id
    """, product_id=event.product_id)

    # Option 2: Invalidate cache
    cache.delete(f"product:{event.product_id}")
    cache.delete("product_list")
    cache.delete("dashboard")

    # Option 3: Update search index
    search_index.index_product(event.product_id)
```

---

## Usage Examples

### Example 1: Create Product (Command)

```python
from core.cqrs import CreateProductCommand
from core.cqrs.handlers import CreateProductCommandHandler

# Initialize handler
product_service = ProductService()
command_handler = CreateProductCommandHandler(product_service)

# Create command
command = CreateProductCommand(
    code="LAPTOP001",
    description="Dell Latitude 5420",
    sell_price=Decimal('1299.99'),
    cost_price=Decimal('950.00'),
    department_id=electronics_dept_id,
    user_id=current_user_id
)

# Execute
result = command_handler.handle(command)

if result.is_success:
    product_id = result.data
    print(f"✓ Product created with ID: {product_id}")

    # Events automatically published:
    # - ProductCreated
    # - Read models automatically updated
else:
    print(f"✗ Failed: {result.error}")
    if result.status == UseCaseStatus.VALIDATION_ERROR:
        for field, error in result.errors.items():
            print(f"  {field}: {error}")
```

### Example 2: Search Products (Query)

```python
from core.cqrs import SearchProductsQuery
from core.cqrs.handlers import SearchProductsQueryHandler

# Initialize handler
query_handler = SearchProductsQueryHandler(product_query_repository)

# Create query
query = SearchProductsQuery(
    search_term="laptop",
    in_stock_only=True,
    limit=20,
    offset=0
)

# Execute
products = query_handler.handle(query)  # List[ProductListItemReadModel]

# Always succeeds (empty list if no results)
print(f"Found {len(products)} products:")
for product in products:
    print(f"  {product.code}: {product.description} - ${product.sell_price}")
    print(f"    In stock: {product.quantity_in_stock}")
    print(f"    Department: {product.department_name}")
```

### Example 3: Get Product Details (Query)

```python
from core.cqrs import GetProductByIdQuery

query = GetProductByIdQuery(product_id=product_id)
product = query_handler.handle(query)  # ProductReadModel or None

if product:
    # Rich denormalized data
    print(f"Code: {product.code}")
    print(f"Description: {product.description}")
    print(f"Price: ${product.sell_price}")
    print(f"Department: {product.department_name}")  # No JOIN needed!
    print(f"Unit: {product.unit_name}")  # No JOIN needed!
    print(f"In Stock: {product.in_stock}")  # Pre-calculated!
    print(f"Low Stock: {product.is_low_stock}")  # Pre-calculated!
    print(f"Stock Value: ${product.stock_value}")  # Pre-calculated!
else:
    print("Product not found")
```

### Example 4: Complex Sale Processing (Command)

```python
from core.cqrs import ProcessSaleCommand, SaleItemCommand

command = ProcessSaleCommand(
    items=[
        SaleItemCommand(product_code="LAPTOP001", quantity=Decimal('1')),
        SaleItemCommand(product_code="MOUSE001", quantity=Decimal('2')),
    ],
    customer_id=customer_id,
    payment_type="credit",
    paid_amount=Decimal('0'),
    user_id=current_user_id
)

result = command_handler.handle(command)

if result.is_success:
    sale_id = result.data

    # Events published:
    # - SaleStarted
    # - SaleItemAdded (×2)
    # - SaleCompleted
    # - InventoryAdjusted (×2)
    # - CustomerBalanceChanged
    #
    # Read models updated:
    # - Sales summary
    # - Customer purchase history
    # - Product sales stats
    # - Dashboard metrics
```

### Example 5: Dashboard Query (Aggregated Data)

```python
from core.cqrs import GetDashboardSummaryQuery

query = GetDashboardSummaryQuery(date=today)
dashboard = query_handler.handle(query)  # DashboardSummaryReadModel

# All data pre-aggregated and denormalized!
print(f"Today's Sales: ${dashboard.today_sales_total} ({dashboard.today_sales_count} transactions)")
print(f"Average Sale: ${dashboard.today_avg_sale}")
print(f"Low Stock Items: {dashboard.low_stock_product_count}")
print(f"Total Inventory Value: ${dashboard.total_inventory_value}")

print("\nRecent Sales:")
for sale in dashboard.recent_sales:
    print(f"  {sale.sale_number}: ${sale.total} - {sale.customer_name}")

# This entire query could be served from cache!
```

---

## Performance Optimizations

### 1. Denormalized Tables

Create denormalized tables/views for common queries:

```sql
CREATE TABLE product_read_view AS
SELECT
    p.id,
    p.code,
    p.description,
    p.sell_price,
    p.cost_price,
    p.quantity_in_stock,
    p.min_stock,
    d.name as department_name,
    u.name as unit_name,
    (p.quantity_in_stock > 0) as in_stock,
    (p.quantity_in_stock < p.min_stock) as is_low_stock,
    (p.quantity_in_stock * p.cost_price) as stock_value
FROM products p
LEFT JOIN departments d ON p.department_id = d.id
LEFT JOIN units u ON p.unit_id = u.id;

-- Create indexes
CREATE INDEX idx_product_read_code ON product_read_view(code);
CREATE INDEX idx_product_read_search ON product_read_view USING gin(to_tsvector('english', code || ' ' || description));
```

Update via event handlers:

```python
@EventPublisher.subscribe(ProductCreated)
@EventPublisher.subscribe(ProductUpdated)
def update_product_read_view(event):
    db.execute("""
        INSERT INTO product_read_view (...)
        SELECT ... FROM products p ...
        WHERE p.id = :product_id
        ON CONFLICT (id) DO UPDATE SET ...
    """, product_id=event.product_id)
```

### 2. Materialized Views

For expensive aggregations:

```sql
CREATE MATERIALIZED VIEW sales_summary_by_day AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as sales_count,
    SUM(total) as total_sales,
    AVG(total) as average_sale,
    SUM(CASE WHEN payment_type = 'cash' THEN total ELSE 0 END) as cash_sales,
    SUM(CASE WHEN payment_type = 'credit' THEN total ELSE 0 END) as credit_sales
FROM sales
GROUP BY DATE(created_at);

-- Refresh periodically or on-demand
REFRESH MATERIALIZED VIEW sales_summary_by_day;
```

### 3. Redis Caching

Cache read models in Redis:

```python
import redis
import json

cache = redis.Redis()

class CachedProductQueryRepository(ProductQueryRepository):
    """Query repository with Redis caching."""

    def get_product_by_id(self, product_id):
        # Try cache first
        cache_key = f"product:{product_id}"
        cached = cache.get(cache_key)

        if cached:
            return ProductReadModel(**json.loads(cached))

        # Cache miss - query database
        product = super().get_product_by_id(product_id)

        if product:
            # Cache for 1 hour
            cache.setex(
                cache_key,
                3600,
                json.dumps(product.__dict__)
            )

        return product

# Invalidate on updates
@EventPublisher.subscribe(ProductUpdated)
def invalidate_product_cache(event):
    cache.delete(f"product:{event.product_id}")
```

### 4. Database Indexes

Optimize queries with appropriate indexes:

```sql
-- Covering index for product search
CREATE INDEX idx_products_search
ON products (department_id, code, description, sell_price, quantity_in_stock)
WHERE is_active = true;

-- Index for low stock query
CREATE INDEX idx_products_low_stock
ON products (quantity_in_stock, min_stock)
WHERE quantity_in_stock < min_stock;

-- Index for sales by date range
CREATE INDEX idx_sales_date_range
ON sales (created_at, customer_id, payment_type, total);
```

---

## Event Integration

CQRS relies heavily on domain events for synchronization:

### Write Side → Events → Read Side

```
1. Command Handler
   ↓
2. Modify Write Model (Products table)
   ↓
3. Publish Event (ProductCreated)
   ↓
4. Event Handler
   ↓
5. Update Read Model (product_read_view)
   ↓
6. Invalidate Cache
   ↓
7. Query Handler sees updated data
```

### Example: Product Price Change Flow

```python
# 1. Command
command = UpdateProductCommand(
    product_id=product_id,
    sell_price=Decimal('149.99')
)

# 2. Command Handler
result = command_handler.handle(command)
# → Updates products table
# → Publishes ProductPriceChanged event

# 3. Event Handlers (run automatically)
@EventPublisher.subscribe(ProductPriceChanged)
def update_product_read_view(event):
    # Update denormalized view
    update_read_view(event.product_id)

@EventPublisher.subscribe(ProductPriceChanged)
def invalidate_caches(event):
    # Invalidate related caches
    cache.delete(f"product:{event.product_id}")
    cache.delete("product_list")
    cache.delete("dashboard")

@EventPublisher.subscribe(ProductPriceChanged)
def update_price_history(event):
    # Add to price history view
    add_price_history_entry(event)

# 4. Query Handler (sees updated data)
query = GetProductByIdQuery(product_id=product_id)
product = query_handler.handle(query)
# → Returns updated price from read view or cache
```

---

## Testing

### Testing Command Handlers

```python
def test_create_product_command():
    """Test command handler with mocked service."""
    # Arrange
    mock_service = Mock(spec=ProductService)
    expected_product = Product(id=UUID('...'), code="TEST", ...)
    mock_service.add_product.return_value = expected_product

    handler = CreateProductCommandHandler(mock_service)
    command = CreateProductCommand(
        code="TEST",
        description="Test Product",
        sell_price=Decimal('99.99')
    )

    # Act
    result = handler.handle(command)

    # Assert
    assert result.is_success
    assert result.data == expected_product.id
    mock_service.add_product.assert_called_once()

def test_create_product_validation_error():
    """Test command validation."""
    handler = CreateProductCommandHandler(Mock())
    command = CreateProductCommand(
        code="",  # Invalid
        description="Test",
        sell_price=Decimal('-10')  # Invalid
    )

    result = handler.handle(command)

    assert result.is_failure
    assert result.status == UseCaseStatus.VALIDATION_ERROR
    assert 'code' in result.errors
    assert 'sell_price' in result.errors
```

### Testing Query Handlers

```python
def test_search_products_query():
    """Test query handler."""
    # Arrange
    mock_repo = Mock(spec=ProductQueryRepository)
    expected_products = [
        ProductListItemReadModel(...),
        ProductListItemReadModel(...),
    ]
    mock_repo.search_products.return_value = expected_products

    handler = SearchProductsQueryHandler(mock_repo)
    query = SearchProductsQuery(search_term="laptop")

    # Act
    result = handler.handle(query)

    # Assert
    assert len(result) == 2
    assert result == expected_products
    mock_repo.search_products.assert_called_once()

def test_query_returns_empty_on_no_results():
    """Test that queries never fail."""
    mock_repo = Mock()
    mock_repo.search_products.return_value = []

    handler = SearchProductsQueryHandler(mock_repo)
    result = handler.handle(SearchProductsQuery(search_term="nonexistent"))

    assert result == []  # Empty list, not None or error
```

### Testing Read Model Updates

```python
def test_read_model_updated_on_event():
    """Test that events update read models."""
    # Arrange
    product_id = uuid4()

    # Subscribe test handler
    updated_products = []

    @EventPublisher.subscribe(ProductCreated)
    def track_updates(event):
        updated_products.append(event.product_id)

    # Act
    event = ProductCreated(
        product_id=product_id,
        code="TEST",
        description="Test",
        sell_price=Decimal('99.99'),
        department_id=None,
        user_id=uuid4()
    )
    EventPublisher.publish(event)

    # Assert
    assert product_id in updated_products
```

---

## Best Practices

### 1. **Keep Commands Small**

```python
# Good - single responsibility
CreateProductCommand
UpdateProductPriceCommand
UpdateProductStockCommand

# Bad - too many responsibilities
UpdateProductCommand  # Updates everything
```

### 2. **Make Queries Specific**

```python
# Good - specific use cases
GetProductForEditQuery  # Returns full product
GetProductForListQuery  # Returns list item
GetProductForSearchQuery  # Returns search result

# Bad - one size fits all
GetProductQuery  # Returns too much or too little
```

### 3. **Never Modify State in Queries**

```python
# Good
class GetProductQueryHandler:
    def handle(self, query):
        return self.repo.get_product(query.id)  # Read only

# Bad
class GetProductQueryHandler:
    def handle(self, query):
        product = self.repo.get_product(query.id)
        product.last_viewed = datetime.now()  # NO! State change!
        return product
```

### 4. **Accept Stale Data for Reads**

```python
# Read models can be slightly out of date
# This is OK for most use cases!

# Customer balance shown: $100
# Actual balance: $102 (sale just completed)
# ← Eventual consistency

# Read model will be updated in milliseconds via events
```

### 5. **Cache Aggressively**

```python
# Queries can be cached heavily
@cache(ttl=300)  # 5 minutes
def get_dashboard_summary():
    return query_handler.handle(GetDashboardSummaryQuery())

# Commands cannot be cached
# (each command is unique and changes state)
```

### 6. **Use Events for Synchronization**

```python
# Don't update read models directly in command handlers
# Bad:
class CreateProductCommandHandler:
    def handle(self, command):
        product = create_product(...)
        update_product_read_view(product)  # NO!
        return product.id

# Good:
class CreateProductCommandHandler:
    def handle(self, command):
        product = create_product(...)
        # Event published automatically
        # Event handler updates read view
        return product.id
```

---

## Summary

CQRS Phase 3 provides:

✅ **Separation**: Commands (writes) separated from Queries (reads)
✅ **Performance**: Denormalized read models, caching, optimized queries
✅ **Scalability**: Scale reads and writes independently
✅ **Clarity**: Clear intent (command = change, query = fetch)
✅ **Flexibility**: Different models for different use cases
✅ **Integration**: Seamless with Domain Events from Phase 1

### Architecture Evolution

**Phase 1**: Domain Events
- Decoupled services
- Event-driven side effects

**Phase 2**: Use Cases / Application Layer
- Clear business operations
- Consistent error handling

**Phase 3**: CQRS ← You are here
- Optimized reads and writes
- Denormalized views
- Better performance

**Next: Phase 4** - Specification Pattern
- Composable queries
- Reusable filters

**Next: Phase 5** - Async Event Processing
- Message queues
- Background processing

---

See `docs/ARCHITECTURE_IMPROVEMENTS.md` for the complete architectural journey!
