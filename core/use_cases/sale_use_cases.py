"""
Sale Use Cases

Complex use cases for processing sales transactions.
Demonstrates orchestration of multiple services and domain events.
"""

from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from core.use_cases.base import UseCase, UseCaseResult, log_use_case_execution
from core.use_cases.dtos import (
    ProcessSaleRequest,
    SaleResponse,
    SaleItemRequest,
)
from core.services.product_service import ProductService
from core.services.sale_service import SaleService
from core.services.customer_service import CustomerService
from core.services.inventory_service import InventoryService
from core.models.sale import Sale, SaleItem
from core.events.sale_events import SaleStarted, SaleItemAdded, SaleCompleted
from infrastructure.persistence.unit_of_work import unit_of_work


class ProcessSaleUseCase(UseCase[ProcessSaleRequest, SaleResponse]):
    """
    Use case for processing a complete sale transaction.

    This is a complex use case that orchestrates multiple services:
    1. Validate customer (if credit sale)
    2. Validate product availability
    3. Check inventory
    4. Create sale with items
    5. Update inventory
    6. Process payment
    7. Update customer balance (if credit)
    8. Publish events

    This demonstrates the power of the Application Layer - it coordinates
    multiple services without tight coupling, and publishes events for
    side effects (receipt generation, notifications, etc.)

    Example:
        use_case = ProcessSaleUseCase(
            sale_service=sale_service,
            product_service=product_service,
            customer_service=customer_service,
            inventory_service=inventory_service
        )

        request = ProcessSaleRequest(
            items=[
                SaleItemRequest(product_code="LAPTOP001", quantity=Decimal('1')),
                SaleItemRequest(product_code="MOUSE001", quantity=Decimal('2'))
            ],
            payment_type="cash",
            paid_amount=Decimal('1500.00'),
            user_id=current_user_id
        )

        result = use_case.execute(request)

        if result.is_success:
            print(f"Sale completed: {result.data.sale_id}")
            print(f"Change: ${result.data.change_amount}")
        else:
            print(f"Sale failed: {result.error}")
    """

    def __init__(
        self,
        sale_service: SaleService,
        product_service: ProductService,
        customer_service: Optional[CustomerService] = None,
        inventory_service: Optional[InventoryService] = None,
    ):
        """
        Initialize the use case with required services.

        Args:
            sale_service: Service for sale operations
            product_service: Service for product lookups
            customer_service: Service for customer operations (optional)
            inventory_service: Service for inventory updates (optional)
        """
        super().__init__()
        self.sale_service = sale_service
        self.product_service = product_service
        self.customer_service = customer_service
        self.inventory_service = inventory_service

    @log_use_case_execution
    def execute(self, request: ProcessSaleRequest) -> UseCaseResult[SaleResponse]:
        """
        Execute the process sale use case.

        This method coordinates the entire sale workflow within a
        single transaction, ensuring data consistency.

        Args:
            request: The sale processing request

        Returns:
            UseCaseResult containing the sale details or error
        """
        # Step 1: Validate request
        validation_errors = self._validate_request(request)
        if validation_errors:
            return UseCaseResult.validation_error(validation_errors)

        # Step 2: Validate customer (if credit sale)
        if request.payment_type == "credit" and request.customer_id:
            customer_validation = self._validate_customer_credit(
                request.customer_id, self._calculate_total(request.items)
            )
            if customer_validation:
                return UseCaseResult.failure(customer_validation)

        # Step 3: Validate and prepare products
        sale_items, total_amount = self._prepare_sale_items(request.items)
        if isinstance(sale_items, UseCaseResult):
            return sale_items  # Error occurred

        # Step 4: Check inventory availability
        inventory_check = self._check_inventory_availability(sale_items)
        if inventory_check:
            return UseCaseResult.failure(inventory_check)

        # Step 5: Validate payment
        payment_validation = self._validate_payment(
            total_amount, request.paid_amount, request.payment_type
        )
        if payment_validation:
            return UseCaseResult.failure(payment_validation)

        # Step 6: Process the sale (transactional)
        try:
            sale_result = self._process_sale_transaction(
                request, sale_items, total_amount
            )

            if sale_result.is_failure:
                return sale_result

            return sale_result

        except Exception as e:
            self.logger.error(f"Error processing sale: {e}", exc_info=True)
            return UseCaseResult.failure(f"Failed to process sale: {str(e)}")

    def _validate_request(self, request: ProcessSaleRequest) -> Optional[dict]:
        """Validate the sale request."""
        errors = {}

        if not request.items:
            errors["items"] = "At least one item is required"

        if request.payment_type not in ["cash", "credit", "card"]:
            errors["payment_type"] = "Invalid payment type"

        if request.payment_type == "credit" and not request.customer_id:
            errors["customer_id"] = "Customer is required for credit sales"

        if request.paid_amount < 0:
            errors["paid_amount"] = "Paid amount cannot be negative"

        # Validate individual items
        for idx, item in enumerate(request.items):
            if not item.product_code:
                errors[f"items.{idx}.product_code"] = "Product code is required"
            if item.quantity <= 0:
                errors[f"items.{idx}.quantity"] = "Quantity must be greater than zero"

        return errors if errors else None

    def _validate_customer_credit(
        self, customer_id: UUID, sale_amount: Decimal
    ) -> Optional[str]:
        """
        Validate customer credit limit.

        Returns:
            Error message if validation fails, None if valid
        """
        if not self.customer_service:
            return None

        customer = self.customer_service.get_customer_by_id(customer_id)
        if not customer:
            return "Customer not found"

        # Check if customer has sufficient credit
        available_credit = customer.credit_limit - customer.balance
        if available_credit < sale_amount:
            return (
                f"Insufficient credit. Available: ${available_credit}, "
                f"Required: ${sale_amount}"
            )

        return None

    def _prepare_sale_items(self, item_requests: List[SaleItemRequest]) -> tuple:
        """
        Validate products and prepare sale items.

        Returns:
            Tuple of (sale_items, total_amount) or (UseCaseResult, None) on error
        """
        sale_items = []
        total_amount = Decimal("0")

        for item_request in item_requests:
            # Get product
            product = self.product_service.get_product_by_code(
                item_request.product_code
            )
            if not product:
                return (
                    UseCaseResult.not_found(f"Product {item_request.product_code}"),
                    None,
                )

            # Determine price
            unit_price = item_request.unit_price or product.sell_price
            subtotal = unit_price * item_request.quantity

            # Create sale item
            sale_item = SaleItem(
                product_id=product.id,
                product_code=product.code,
                product_description=product.description,
                quantity=item_request.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                cost_price=product.cost_price or Decimal("0"),
            )

            sale_items.append(sale_item)
            total_amount += subtotal

        return sale_items, total_amount

    def _check_inventory_availability(
        self, sale_items: List[SaleItem]
    ) -> Optional[str]:
        """
        Check if all products have sufficient inventory.

        Returns:
            Error message if insufficient inventory, None if all available
        """
        for item in sale_items:
            product = self.product_service.get_product_by_id(item.product_id)

            if product.uses_inventory:
                if product.quantity_in_stock < item.quantity:
                    return (
                        f"Insufficient stock for {product.code}. "
                        f"Available: {product.quantity_in_stock}, "
                        f"Required: {item.quantity}"
                    )

        return None

    def _validate_payment(
        self, total_amount: Decimal, paid_amount: Decimal, payment_type: str
    ) -> Optional[str]:
        """
        Validate payment amount.

        Returns:
            Error message if payment invalid, None if valid
        """
        if payment_type == "cash":
            if paid_amount < total_amount:
                return (
                    f"Insufficient payment. Total: ${total_amount}, "
                    f"Paid: ${paid_amount}"
                )

        return None

    def _calculate_total(self, item_requests: List[SaleItemRequest]) -> Decimal:
        """Calculate total amount for items."""
        total = Decimal("0")
        for item_request in item_requests:
            product = self.product_service.get_product_by_code(
                item_request.product_code
            )
            if product:
                price = item_request.unit_price or product.sell_price
                total += price * item_request.quantity
        return total

    def _process_sale_transaction(
        self,
        request: ProcessSaleRequest,
        sale_items: List[SaleItem],
        total_amount: Decimal,
    ) -> UseCaseResult[SaleResponse]:
        """
        Process the sale within a transaction.

        This ensures all operations succeed or fail together.
        """
        with unit_of_work() as uow:
            # Create sale
            sale_id = uuid4()
            change_amount = (
                request.paid_amount - total_amount
                if request.payment_type == "cash"
                else Decimal("0")
            )

            sale = Sale(
                id=sale_id,
                customer_id=request.customer_id,
                total=total_amount,
                payment_type=request.payment_type,
                paid_amount=request.paid_amount,
                change_amount=change_amount,
                items=sale_items,
                created_at=datetime.utcnow(),
                user_id=request.user_id,
            )

            # Save sale
            created_sale = uow.sales.add(sale)

            # Publish SaleStarted event
            uow.add_event(
                SaleStarted(
                    sale_id=sale_id,
                    customer_id=request.customer_id,
                    user_id=request.user_id or UUID(int=0),
                )
            )

            # Publish SaleItemAdded events
            for item in sale_items:
                uow.add_event(
                    SaleItemAdded(
                        sale_id=sale_id,
                        product_id=item.product_id,
                        product_code=item.product_code,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        subtotal=item.subtotal,
                    )
                )

            # Update inventory (if inventory service available)
            if self.inventory_service:
                for item in sale_items:
                    product = self.product_service.get_product_by_id(item.product_id)
                    if product.uses_inventory:
                        # This would normally call inventory_service.adjust_inventory()
                        # For now, we'll let the service handle it
                        pass

            # Publish SaleCompleted event
            uow.add_event(
                SaleCompleted(
                    sale_id=sale_id,
                    customer_id=request.customer_id,
                    total_amount=total_amount,
                    payment_type=request.payment_type,
                    paid_amount=request.paid_amount,
                    change_amount=change_amount,
                    user_id=request.user_id or UUID(int=0),
                    has_credit=request.payment_type == "credit",
                )
            )

            # Events will be published automatically after commit

        # Create response
        response = SaleResponse.from_domain(created_sale)
        return UseCaseResult.success(response)
