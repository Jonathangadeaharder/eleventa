## Code Review for TASK-027: Feature - Customer Credits (Basic)

**Files Reviewed:**

*   `core/models/customer.py`
*   `core/models/credit.py`
*   `infrastructure/persistence/sqlite/models_mapping.py`
*   `core/interfaces/repository_interfaces.py`
*   `infrastructure/persistence/sqlite/repositories.py`
*   `core/services/sale_service.py`
*   `core/services/customer_service.py`
*   `ui/views/sales_view.py`

**Summary:**

The code implements basic credit functionality, allowing sales to be associated with customers and tracking customer balances. The `Customer`, `CreditPayment`, `Sale`, and related ORM models and repositories have been updated to support this functionality.

**Recommendations:**

*   Implement credit limit checking in `core/services/customer_service.py`.
*   Add UI for viewing customer balances and registering payments.
*   Consider adding a dedicated `CreditService` to handle credit-related business logic.

**Detailed Comments:**

*   **Models:** The `Customer` model includes `credit_limit` and `credit_balance` attributes, which is necessary for tracking customer credits. The `CreditPayment` model represents a payment made towards a customer's credit account.
*   **ORM Mapping:** The `CustomerOrm` model includes `credit_limit` and `credit_balance` columns, which map to the corresponding attributes in the `Customer` model. The `CreditPaymentOrm` model maps to the `CreditPayment` model. Relationships are defined between `CustomerOrm` and `SaleOrm` (one-to-many) and `CustomerOrm` and `CreditPaymentOrm` (one-to-many).
*   **Repository Interfaces:** The `ICustomerRepository` interface includes methods for `add`, `get_by_id`, `get_all`, `update`, `delete`, `search`, `get_by_cuit`, and `update_balance`. The `ICreditPaymentRepository` interface includes methods for `add`, `get_by_id`, and `get_for_customer`.
*   **Repository Implementations:** The `SqliteCustomerRepository` implements the `ICustomerRepository` interface. It includes methods for adding, getting, updating, and deleting customers. It also includes a method for updating the credit balance (`update_balance`). The `SqliteCreditPaymentRepository` implements the `ICreditPaymentRepository` interface. It includes methods for adding and getting credit payments.
*   **Sale Service:** The `create_sale` method in `SaleService` now accepts `customer_id` and `is_credit_sale` parameters. If `is_credit_sale` is True, the `increase_customer_debt` method in `CustomerService` is called to update the customer's credit balance.
*   **Customer Service:** The `CustomerService` includes methods for `apply_payment` and `increase_customer_debt`. The `apply_payment` method updates the customer's credit balance and logs the payment. The `increase_customer_debt` method increases the customer's debt (decreases the credit balance).
*   **Sales View:** The `SalesView` includes a `PaymentDialog` for selecting the payment method. The `finalize_current_sale` method now passes the `customer_id`, `payment_method`, and `is_credit` parameters to the `create_sale` method in `SaleService`.
