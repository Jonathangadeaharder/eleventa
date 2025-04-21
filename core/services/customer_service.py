import re
from decimal import Decimal
from typing import Optional, List, Callable, Any

from core.models.customer import Customer
from core.models.credit import CreditPayment
from core.interfaces.repository_interfaces import ICustomerRepository, ICreditPaymentRepository
from infrastructure.persistence.utils import session_scope
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Basic email regex (adjust as needed for stricter validation)
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

RepositoryFactory = Callable[[Session], Any]

class CustomerService:
    def __init__(self, customer_repo_factory: RepositoryFactory,
                 credit_payment_repo_factory: RepositoryFactory):
        self._customer_repo_factory = customer_repo_factory
        self._credit_payment_repo_factory = credit_payment_repo_factory

    def _validate_customer_data(self, name: str, email: str | None):
        if not name:
            raise ValueError("Customer name cannot be empty")
        if email and not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format")
        # Add other validation rules here (e.g., phone format, duplicate checks if not handled by DB)

    def add_customer(self, name: str, phone: str | None = None, email: str | None = None, address: str | None = None, credit_limit: Decimal = Decimal('0.00'), credit_balance: Decimal = Decimal('0.00')) -> Customer:
        self._validate_customer_data(name, email)
        with session_scope() as session:
            repo = self._customer_repo_factory(session)
            # Potential duplicate checks here using repo
            new_customer = Customer(
                id=None, # ID will be assigned by the repository/DB
                name=name,
                phone=phone,
                email=email,
                address=address,
                credit_limit=credit_limit,
                credit_balance=credit_balance
            )
            added = repo.add(new_customer)
            logger.info(f"Added customer: {added.name} (ID: {added.id})")
            return added

    def update_customer(self, customer_id: int, name: str, phone: str | None = None, email: str | None = None, address: str | None = None, credit_limit: Decimal = Decimal('0.00')) -> Customer:
        self._validate_customer_data(name, email)
        with session_scope() as session:
            repo = self._customer_repo_factory(session)
            customer_to_update = repo.get_by_id(customer_id)
            if not customer_to_update:
                raise ValueError(f"Customer with ID {customer_id} not found")

            # Keep original balance (ensure it's Decimal)
            original_balance = customer_to_update.credit_balance if isinstance(customer_to_update.credit_balance, Decimal) else Decimal(str(customer_to_update.credit_balance))

            # Update fields (excluding credit_balance)
            customer_to_update.name = name
            customer_to_update.phone = phone
            customer_to_update.email = email
            customer_to_update.address = address
            customer_to_update.credit_limit = credit_limit

            updated_customer_obj = repo.update(customer_to_update)

            # Restore original balance in the returned object as repo.update might overwrite it
            # The actual balance in DB should be unchanged if repo.update doesn't touch it
            if updated_customer_obj:
                 updated_customer_obj.credit_balance = original_balance
                 logger.info(f"Updated customer info: {updated_customer_obj.name} (ID: {updated_customer_obj.id})")
                 return updated_customer_obj
            else:
                 # Should ideally not happen if get_by_id worked, but handle case
                 logger.error(f"Failed to update customer {customer_id} in repository.")
                 # Return the original object perhaps, or raise error?
                 # For now, return the object we tried to update, with original balance restored
                 customer_to_update.credit_balance = original_balance
                 return customer_to_update

    def delete_customer(self, customer_id: int) -> bool:
        with session_scope() as session:
            repo = self._customer_repo_factory(session)
            customer_to_delete = repo.get_by_id(customer_id)
            if not customer_to_delete:
                # Or just return False silently?
                logger.warning(f"Attempted to delete non-existent customer ID: {customer_id}")
                return False

            # Constraint check (ensure balance is Decimal)
            balance = customer_to_delete.credit_balance if isinstance(customer_to_delete.credit_balance, Decimal) else Decimal(str(customer_to_delete.credit_balance))
            if balance is not None and abs(balance) > Decimal('0.001'):
                raise ValueError(f"Cannot delete customer {customer_to_delete.name} with an outstanding balance ({balance:.2f})")

            deleted = repo.delete(customer_id)
            if deleted:
                 logger.info(f"Deleted customer ID: {customer_id}")
            return deleted

    def find_customer(self, search_term: str) -> list[Customer]:
         with session_scope() as session:
            repo = self._customer_repo_factory(session)
            return repo.search(search_term)

    def get_customer_by_id(self, customer_id: int) -> Customer | None:
        with session_scope() as session:
            repo = self._customer_repo_factory(session)
            return repo.get_by_id(customer_id)

    def get_all_customers(self) -> list[Customer]:
         with session_scope() as session:
            repo = self._customer_repo_factory(session)
            return repo.get_all()

    # --- Methods related to Credit (Implementation for TASK-027) ---

    def apply_payment(self, customer_id: int, amount: Decimal, notes: str | None = None, user_id: Optional[int] = None) -> CreditPayment:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        with session_scope() as session:
            # Get repos within session
            cust_repo = self._customer_repo_factory(session)
            pay_repo = self._credit_payment_repo_factory(session)

            customer = cust_repo.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")

            current_balance = Decimal(str(customer.credit_balance))
            new_balance = current_balance + amount # Payment increases balance (reduces debt)

            # Update balance using the repo (assuming repo method accepts Decimal or converts)
            # If repo.update_balance expects float, conversion needed here
            updated = cust_repo.update_balance(customer_id, new_balance)
            if not updated:
                raise Exception(f"Failed to update balance for customer ID {customer_id}")

            # Log the payment
            payment_log = CreditPayment(
                customer_id=customer_id,
                amount=amount,
                notes=notes,
                user_id=user_id
            )
            created_payment = pay_repo.add(payment_log)
            logger.info(f"Applied payment {created_payment.id} of {amount} to customer {customer_id}. New balance: {new_balance:.2f}")
            return created_payment

    def increase_customer_debt(self, customer_id: int, amount: Decimal, session: Session):
        if amount <= 0:
            # Should be positive amount representing the value of goods/services
            raise ValueError("Amount to increase debt must be positive.")

        # Use the *passed* session to get repo instances
        cust_repo = self._customer_repo_factory(session)

        customer = cust_repo.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found within transaction.")

        current_balance = Decimal(str(customer.credit_balance))
        new_balance = current_balance - amount # Debt increases, balance decreases

        # Update balance using the repo (assuming repo method accepts Decimal or converts)
        updated = cust_repo.update_balance(customer_id, new_balance)
        if not updated:
             raise Exception(f"Failed to update balance for customer ID {customer_id} within transaction.")
        logger.info(f"Increased debt for customer {customer_id} by {amount}. New balance: {new_balance:.2f}")

    def get_customer_payments(self, customer_id: int) -> List[CreditPayment]:
        with session_scope() as session:
            repo = self._credit_payment_repo_factory(session)
            return repo.get_for_customer(customer_id)

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