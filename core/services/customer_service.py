import re
from decimal import Decimal
from typing import Optional, List, Any
import uuid

from core.models.customer import Customer
from core.models.credit_payment import CreditPayment
from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import unit_of_work
import logging

logger = logging.getLogger(__name__)

# Basic email regex (adjust as needed for stricter validation)
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class CustomerService(ServiceBase):
    def __init__(self):
        """
        Initialize the customer service.
        """
        super().__init__()  # Initialize base class with default logger

    def _validate_customer_data(self, name: str, email: str | None):
        """Validate customer data."""
        if not name:
            raise ValueError("Customer name cannot be empty")
        if email and not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format")
        # Add other validation rules here (e.g., phone format, duplicate checks if not handled by DB)

    def add_customer(
        self,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        credit_limit: Decimal = Decimal("0.00"),
        credit_balance: Decimal = Decimal("0.00"),
    ) -> Customer:
        """Add a new customer."""
        with unit_of_work() as uow:
            self._validate_customer_data(name, email)

            # Potential duplicate checks here using repo
            new_customer = Customer(
                id=None,  # ID will be assigned by the repository/DB
                name=name,
                phone=phone,
                email=email,
                address=address,
                credit_limit=credit_limit,
                credit_balance=credit_balance,
            )
            added = uow.customers.add(new_customer)
            self.logger.info(f"Added customer: {added.name} (ID: {added.id})")
            return added

    def update_customer(
        self,
        customer_id: int,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        credit_limit: Decimal = Decimal("0.00"),
    ) -> Customer:
        """Update an existing customer."""
        with unit_of_work() as uow:
            self._validate_customer_data(name, email)

            customer_to_update = uow.customers.get_by_id(customer_id)
            if not customer_to_update:
                raise ValueError(f"Customer with ID {customer_id} not found")

            # Keep original balance (ensure it's Decimal)
            original_balance = (
                customer_to_update.credit_balance
                if isinstance(customer_to_update.credit_balance, Decimal)
                else Decimal(str(customer_to_update.credit_balance))
            )

            # Update fields (excluding credit_balance)
            customer_to_update.name = name
            customer_to_update.phone = phone
            customer_to_update.email = email
            customer_to_update.address = address
            customer_to_update.credit_limit = credit_limit

            updated_customer_obj = uow.customers.update(customer_to_update)

            # Restore original balance in the returned object as repo.update might overwrite it
            # The actual balance in DB should be unchanged if repo.update doesn't touch it
            if updated_customer_obj:
                updated_customer_obj.credit_balance = original_balance
                self.logger.info(
                    f"Updated customer info: {updated_customer_obj.name} (ID: {updated_customer_obj.id})"
                )
                return updated_customer_obj
            else:
                # Should ideally not happen if get_by_id worked, but handle case
                self.logger.error(
                    f"Failed to update customer {customer_id} in repository."
                )
                # Return the original object perhaps, or raise error?
                # For now, return the object we tried to update, with original balance restored
                customer_to_update.credit_balance = original_balance
                return customer_to_update

    def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer."""
        with unit_of_work() as uow:
            customer_to_delete = uow.customers.get_by_id(customer_id)
            if not customer_to_delete:
                # Or just return False silently?
                self.logger.warning(
                    f"Attempted to delete non-existent customer ID: {customer_id}"
                )
                return False

            # Constraint check (ensure balance is Decimal)
            balance = (
                customer_to_delete.credit_balance
                if isinstance(customer_to_delete.credit_balance, Decimal)
                else Decimal(str(customer_to_delete.credit_balance))
            )
            if balance is not None and abs(balance) > Decimal("0.001"):
                raise ValueError(
                    f"Cannot delete customer {customer_to_delete.name} with an outstanding balance ({balance:.2f})"
                )

            # Check for any payment records and delete them first
            payments = uow.credit_payments.get_for_customer(customer_id)
            if payments:
                # Delete all payment records for this customer
                self.logger.info(
                    f"Deleting {len(payments)} payment records for customer {customer_id}"
                )
                for payment in payments:
                    uow.credit_payments.delete(payment.id)

            # Now safe to delete the customer
            deleted = uow.customers.delete(customer_id)
            if deleted:
                self.logger.info(f"Deleted customer ID: {customer_id}")
            return deleted

    def find_customer(
        self,
        search_term: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[Customer]:
        """Find customers matching the search term, with optional pagination."""
        with unit_of_work() as uow:
            return uow.customers.search(search_term, limit=limit, offset=offset)

    def get_customer_by_id(self, customer_id: Any) -> Customer | None:
        """
        Get a customer by ID, supports both integer and UUID customer IDs.

        Args:
            customer_id: Customer ID (can be int or UUID)

        Returns:
            Customer object if found, None otherwise
        """
        with unit_of_work() as uow:
            customer = uow.customers.get_by_id(customer_id)
            if customer:
                return customer

            # Log the failure for debugging
            self.logger.debug(
                f"Customer with ID {customer_id} (type={type(customer_id)}) not found"
            )
            return None

    def get_all_customers(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[Customer]:
        """Get all customers, with optional pagination."""
        with unit_of_work() as uow:
            return uow.customers.get_all(limit=limit, offset=offset)

    # --- Methods related to Credit (Implementation for TASK-027) ---

    def apply_payment(
        self,
        customer_id: uuid.UUID,
        amount: Decimal,
        notes: str | None = None,
        user_id: Optional[int] = None,
    ) -> CreditPayment:
        """Apply a payment to a customer's account."""
        with unit_of_work() as uow:
            if amount <= 0:
                raise ValueError("Payment amount must be positive.")

            customer = uow.customers.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")

            current_balance = Decimal(str(customer.credit_balance))
            new_balance = (
                current_balance + amount
            )  # Payment increases balance (follows test expectations)

            # Update balance using the repo (assuming repo method accepts Decimal or converts)
            # If repo.update_balance expects float, conversion needed here
            updated = uow.customers.update_balance(customer_id, new_balance)
            if not updated:
                raise Exception(
                    f"Failed to update balance for customer ID {customer_id}"
                )

            # Create the payment log with the customer's actual UUID
            payment_log = CreditPayment(
                customer_id=customer_id,  # Use the customer_id UUID directly
                amount=amount,
                notes=notes,
                user_id=user_id,
            )
            created_payment = uow.credit_payments.add(payment_log)
            self.logger.info(
                f"Applied payment {created_payment.id} of {amount} to customer {customer_id}. New balance: {new_balance:.2f}. User ID for CreditPayment: {user_id} (type: {type(user_id)})"
            )
            return created_payment

    def increase_customer_debt(self, customer_id: int, amount: Decimal) -> None:
        """
        Increase a customer's debt.

        Args:
            customer_id: The ID of the customer
            amount: The amount to increase debt by (must be positive)
        """
        with unit_of_work() as uow:
            if amount <= 0:
                # Should be positive amount representing the value of goods/services
                raise ValueError("Amount to increase debt must be positive.")

            customer = uow.customers.get_by_id(customer_id)
            if not customer:
                raise ValueError(
                    f"Customer with ID {customer_id} not found within transaction."
                )

            current_balance = Decimal(str(customer.credit_balance))
            new_balance = current_balance - amount  # Debt increases, balance decreases

            # Update balance using the repo (assuming repo method accepts Decimal or converts)
            updated = uow.customers.update_balance(customer_id, new_balance)
            if not updated:
                raise Exception(
                    f"Failed to update balance for customer ID {customer_id} within transaction."
                )

            self.logger.info(
                f"Increased debt for customer {customer_id} by {amount}. New balance: {new_balance:.2f}"
            )

    def get_customer_payments(self, customer_id: int) -> List[CreditPayment]:
        """Get all payments for a customer."""
        with unit_of_work() as uow:
            return uow.credit_payments.get_for_customer(customer_id)

    # Optional: Credit Limit Check
    # def check_credit_limit(self, customer_id: int, proposed_increase: Decimal) -> bool:
    #     """Checks if adding a proposed debt increase exceeds the customer's credit limit."""
    #     customer = self.get_customer_by_id(customer_id)
    #     if not customer:
    #         raise ValueError(f"Customer with ID {customer_id} not found.")
    #     if customer.credit_limit is None or customer.credit_limit <= 0:
    #         return True # No limit set or limit is zero/negative, allow any debt
    #
    #     current_balance = Decimal(str(customer.credit_balance))
    #     potential_debt = abs(current_balance - proposed_increase)
    #
    #     return potential_debt <= Decimal(str(customer.credit_limit))

    # Ensure update_customer doesn't directly modify credit_balance
    # It should only be modified via apply_payment or increase_customer_debt
    # def update_customer(self, customer_id: int, name: str, phone: str | None = None, email: str | None = None, address: str | None = None, credit_limit: float = 0.0) -> Customer:
    #     self._validate_customer_data(name, email)
    #
    #     customer_to_update = self.get_customer_by_id(customer_id)
    #     if not customer_to_update:
    #         raise ValueError(f"Customer with ID {customer_id} not found")
    #
    #     # Update fields (excluding credit_balance)
    #     customer_to_update.name = name
    #     customer_to_update.phone = phone
    #     customer_to_update.email = email
    #     customer_to_update.address = address
    #     customer_to_update.credit_limit = credit_limit
    #
    #     # Call the repo update method, which should persist these changes
    #     # Note: The repo's update method might update all fields based on the passed object.
    #     # It might be better to have a specific repo method that avoids balance update,
    #     # or ensure the object passed to repo.update() has the *original* balance.
    #     # For simplicity now, we rely on the repo's update method behavior.
    #     # Let's fetch the original balance before updating the object
    #     original_balance = customer_to_update.credit_balance
    #     updated_customer_obj = self._customer_repo.update(customer_to_update)
    #     # Ensure the balance wasn't accidentally changed by the generic update
    #     if abs(updated_customer_obj.credit_balance - original_balance) > 0.001:
    #          log.warning(f"Customer {customer_id} balance was unexpectedly changed during update_customer call.")
    #          # Optionally, force setting it back, though this indicates a flaw in repo.update
    #          # self._customer_repo.update_balance(customer_id, original_balance)
    #          updated_customer_obj.credit_balance = original_balance # Correct the returned object
    #
    #     return updated_customer_obj

    def adjust_balance(
        self,
        customer_id: uuid.UUID,
        amount: Decimal,
        is_increase: bool,
        notes: str,
        user_id: Optional[int] = None,
    ) -> CreditPayment:
        """
        Directly adjust a customer's balance.

        Args:
            customer_id: The customer ID
            amount: The amount to adjust (always positive)
            is_increase: If True, increase debt (decrease balance), if False, decrease debt (increase balance)
            notes: Explanation for this adjustment (required)
            user_id: Optional ID of the user making the adjustment

        Returns:
            The created CreditPayment entry logging this adjustment
        """
        with unit_of_work() as uow:
            if amount <= 0:
                raise ValueError("Adjustment amount must be positive.")

            if not notes:
                raise ValueError("Notes are required for balance adjustments.")

            customer = uow.customers.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")

            current_balance = Decimal(str(customer.credit_balance))

            # Apply the adjustment based on direction
            if is_increase:
                # Increase debt means adding to the balance (positive = debt)
                new_balance = current_balance + amount
                adjustment_type = "increase"
            else:
                # Decrease debt means reducing the balance
                if amount > current_balance and current_balance > 0:
                    # If adjustment would make balance negative, warn or limit
                    # For now, we'll allow negative balances (customer has credit)
                    self.logger.warning(
                        f"Adjustment of {amount} exceeds customer's current balance {current_balance}"
                    )

                new_balance = current_balance - amount
                adjustment_type = "decrease"

            # Update balance
            updated = uow.customers.update_balance(customer_id, new_balance)
            if not updated:
                raise Exception(
                    f"Failed to update balance for customer ID {customer_id}"
                )

            # Use negative amount for decreases to distinguish from payments in the logs
            log_amount = amount if is_increase else -amount

            # Create the payment/adjustment log with the customer's actual UUID
            self.logger.debug(
                f"_adjust_balance: Attempting to create CreditPayment with user_id: {user_id} (type: {type(user_id)})"
            )
            payment_log = CreditPayment(
                customer_id=customer_id,  # Use the customer_id UUID directly
                amount=log_amount,
                notes=f"[BALANCE ADJUSTMENT - {adjustment_type.upper()}] {notes}",
                user_id=user_id,
            )
            created_record = uow.credit_payments.add(payment_log)
            self.logger.info(
                f"Balance adjustment ({adjustment_type}) of {amount} applied to customer {customer_id}. "
                f"Old balance: {current_balance:.2f}, New balance: {new_balance:.2f}. "
                f"User ID for CreditPayment: {user_id} (type: {type(user_id)})"
            )
            return created_record
