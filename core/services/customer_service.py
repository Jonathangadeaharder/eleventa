import re
from decimal import Decimal
from typing import Optional, List, Callable, Any
from sqlalchemy.orm import Session
import uuid

from core.models.customer import Customer
from core.models.credit_payment import CreditPayment
from core.interfaces.repository_interfaces import ICustomerRepository, ICreditPaymentRepository
from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope
import logging

logger = logging.getLogger(__name__)

# Basic email regex (adjust as needed for stricter validation)
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

class CustomerService(ServiceBase):
    def __init__(self, customer_repo_factory: Callable[[Session], ICustomerRepository],
                 credit_payment_repo_factory: Callable[[Session], ICreditPaymentRepository]):
        """
        Initialize with repository factories.
        
        Args:
            customer_repo_factory: Factory function to create customer repository
            credit_payment_repo_factory: Factory function to create credit payment repository
        """
        super().__init__()  # Initialize base class with default logger
        self._customer_repo_factory = customer_repo_factory
        self._credit_payment_repo_factory = credit_payment_repo_factory

    def _validate_customer_data(self, name: str, email: str | None):
        """Validate customer data."""
        if not name:
            raise ValueError("Customer name cannot be empty")
        if email and not re.match(EMAIL_REGEX, email):
            raise ValueError("Invalid email format")
        # Add other validation rules here (e.g., phone format, duplicate checks if not handled by DB)

    def add_customer(self, name: str, phone: str | None = None, email: str | None = None, 
                    address: str | None = None, credit_limit: Decimal = Decimal('0.00'), 
                    credit_balance: Decimal = Decimal('0.00')) -> Customer:
        """Add a new customer."""
        def _add_customer(session, name, phone, email, address, credit_limit, credit_balance):
            self._validate_customer_data(name, email)
            repo = self._get_repository(self._customer_repo_factory, session)
            
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
            self.logger.info(f"Added customer: {added.name} (ID: {added.id})")
            return added
            
        return self._with_session(_add_customer, name, phone, email, address, credit_limit, credit_balance)

    def update_customer(self, customer_id: int, name: str, phone: str | None = None, 
                        email: str | None = None, address: str | None = None, 
                        credit_limit: Decimal = Decimal('0.00')) -> Customer:
        """Update an existing customer."""
        def _update_customer(session, customer_id, name, phone, email, address, credit_limit):
            self._validate_customer_data(name, email)
            repo = self._get_repository(self._customer_repo_factory, session)
            
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
                self.logger.info(f"Updated customer info: {updated_customer_obj.name} (ID: {updated_customer_obj.id})")
                return updated_customer_obj
            else:
                # Should ideally not happen if get_by_id worked, but handle case
                self.logger.error(f"Failed to update customer {customer_id} in repository.")
                # Return the original object perhaps, or raise error?
                # For now, return the object we tried to update, with original balance restored
                customer_to_update.credit_balance = original_balance
                return customer_to_update
                
        return self._with_session(_update_customer, customer_id, name, phone, email, address, credit_limit)

    def delete_customer(self, customer_id: int) -> bool:
        """Delete a customer."""
        def _delete_customer(session, customer_id):
            repo = self._get_repository(self._customer_repo_factory, session)
            
            customer_to_delete = repo.get_by_id(customer_id)
            if not customer_to_delete:
                # Or just return False silently?
                self.logger.warning(f"Attempted to delete non-existent customer ID: {customer_id}")
                return False

            # Constraint check (ensure balance is Decimal)
            balance = customer_to_delete.credit_balance if isinstance(customer_to_delete.credit_balance, Decimal) else Decimal(str(customer_to_delete.credit_balance))
            if balance is not None and abs(balance) > Decimal('0.001'):
                raise ValueError(f"Cannot delete customer {customer_to_delete.name} with an outstanding balance ({balance:.2f})")

            deleted = repo.delete(customer_id)
            if deleted:
                self.logger.info(f"Deleted customer ID: {customer_id}")
            return deleted
            
        return self._with_session(_delete_customer, customer_id)

    def find_customer(self, search_term: str, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Customer]:
        """Find customers matching the search term, with optional pagination."""
        def _find_customer(session, search_term, limit, offset):
            repo = self._get_repository(self._customer_repo_factory, session)
            return repo.search(search_term, limit=limit, offset=offset)
            
        return self._with_session(_find_customer, search_term, limit, offset)

    def get_customer_by_id(self, customer_id: Any) -> Customer | None:
        """
        Get a customer by ID, supports both integer and UUID customer IDs.
        
        Args:
            customer_id: Customer ID (can be int or UUID)
            
        Returns:
            Customer object if found, None otherwise
        """
        def _get_customer_by_id(session, customer_id):
            repo = self._get_repository(self._customer_repo_factory, session)
            customer = repo.get_by_id(customer_id)
            if customer:
                return customer
                
            # Log the failure for debugging
            self.logger.debug(f"Customer with ID {customer_id} (type={type(customer_id)}) not found")
            return None
            
        return self._with_session(_get_customer_by_id, customer_id)

    def get_all_customers(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[Customer]:
        """Get all customers, with optional pagination."""
        def _get_all_customers(session, limit, offset):
            repo = self._get_repository(self._customer_repo_factory, session)
            return repo.get_all(limit=limit, offset=offset)
            
        return self._with_session(_get_all_customers, limit, offset)

    # --- Methods related to Credit (Implementation for TASK-027) ---

    def apply_payment(self, customer_id: int, amount: Decimal, notes: str | None = None, user_id: Optional[int] = None) -> CreditPayment:
        """Apply a payment to a customer's account."""
        def _apply_payment(session, customer_id, amount, notes, user_id):
            if amount <= 0:
                raise ValueError("Payment amount must be positive.")

            # Get repos within session
            cust_repo = self._get_repository(self._customer_repo_factory, session)
            pay_repo = self._get_repository(self._credit_payment_repo_factory, session)

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

            # Convert integer customer_id to UUID format
            customer_uuid = uuid.UUID(f'00000000-0000-0000-0000-{customer_id:012d}')
            
            # Log the payment
            payment_log = CreditPayment(
                customer_id=customer_uuid,
                amount=amount,
                notes=notes,
                user_id=user_id
            )
            created_payment = pay_repo.add(payment_log)
            self.logger.info(f"Applied payment {created_payment.id} of {amount} to customer {customer_id}. New balance: {new_balance:.2f}")
            return created_payment
            
        return self._with_session(_apply_payment, customer_id, amount, notes, user_id)

    def increase_customer_debt(self, customer_id: int, amount: Decimal, session: Optional[Session] = None) -> None:
        """
        Increase a customer's debt.
        
        Args:
            customer_id: The ID of the customer
            amount: The amount to increase debt by (must be positive)
            session: Optional session to use (for transaction sharing)
        """
        def _increase_customer_debt(session, customer_id, amount):
            if amount <= 0:
                # Should be positive amount representing the value of goods/services
                raise ValueError("Amount to increase debt must be positive.")

            # Get repository from factory
            cust_repo = self._get_repository(self._customer_repo_factory, session)

            customer = cust_repo.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found within transaction.")

            current_balance = Decimal(str(customer.credit_balance))
            new_balance = current_balance - amount # Debt increases, balance decreases

            # Update balance using the repo (assuming repo method accepts Decimal or converts)
            updated = cust_repo.update_balance(customer_id, new_balance)
            if not updated:
                raise Exception(f"Failed to update balance for customer ID {customer_id} within transaction.")
                
            self.logger.info(f"Increased debt for customer {customer_id} by {amount}. New balance: {new_balance:.2f}")
            
        # If session is provided, use it directly; otherwise use _with_session
        if session:
            return _increase_customer_debt(session, customer_id, amount)
        else:
            return self._with_session(_increase_customer_debt, customer_id, amount)

    def get_customer_payments(self, customer_id: int) -> List[CreditPayment]:
        """Get all payments for a customer."""
        def _get_customer_payments(session, customer_id):
            repo = self._get_repository(self._credit_payment_repo_factory, session)
            return repo.get_for_customer(customer_id)
            
        return self._with_session(_get_customer_payments, customer_id)

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