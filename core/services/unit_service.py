from typing import List, Optional
from core.models.unit import Unit
from core.services.service_base import ServiceBase
from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work
from core.utils.validation import validate_required_field


class UnitService(ServiceBase):
    """Service for unit management using Unit of Work pattern."""
    
    def __init__(self):
        """
        Initialize the service.
        """
        super().__init__()  # Initialize base class with default logger

    def _validate_unit(self, unit: Unit, is_update: bool = False, existing_unit_id: Optional[int] = None):
        """Common validation logic for adding/updating units."""
        # Validate required fields
        validate_required_field(unit.name, "Name")
        validate_required_field(unit.abbreviation, "Abbreviation")
        
        # Validate name length
        if len(unit.name) > 50:
            raise ValueError("Unit name cannot exceed 50 characters.")
            
        # Validate abbreviation length
        if len(unit.abbreviation) > 10:
            raise ValueError("Unit abbreviation cannot exceed 10 characters.")

    def add_unit(self, unit: Unit) -> Unit:
        """Add a new unit."""
        with unit_of_work() as uow:
            try:
                self._validate_unit(unit)
                
                # Check for duplicate name
                existing = uow.units.get_by_name(unit.name)
                if existing:
                    raise ValueError(f"Unit name '{unit.name}' already exists.")
                
                # Add the unit
                added_unit = uow.units.add(unit)
                uow.commit()
                
                self.logger.info(f"Unit added successfully: {added_unit.name} (ID: {added_unit.id})")
                return added_unit
                
            except Exception as e:
                self.logger.error(f"Error adding unit: {e}")
                uow.rollback()
                raise

    def get_unit_by_id(self, unit_id: int) -> Optional[Unit]:
        """Get a unit by its ID."""
        with unit_of_work() as uow:
            try:
                return uow.units.get_by_id(unit_id)
            except Exception as e:
                self.logger.error(f"Error retrieving unit by ID {unit_id}: {e}")
                raise

    def get_unit_by_name(self, name: str) -> Optional[Unit]:
        """Get a unit by its name."""
        with unit_of_work() as uow:
            try:
                return uow.units.get_by_name(name)
            except Exception as e:
                self.logger.error(f"Error retrieving unit by name '{name}': {e}")
                raise

    def get_all_units(self, active_only: bool = True) -> List[Unit]:
        """Get all units, optionally filtered by active status."""
        with unit_of_work() as uow:
            try:
                return uow.units.get_all(active_only=active_only)
            except Exception as e:
                self.logger.error(f"Error retrieving units: {e}")
                raise

    def update_unit(self, unit: Unit) -> Unit:
        """Update an existing unit."""
        with unit_of_work() as uow:
            try:
                if unit.id is None:
                    raise ValueError("Unit ID is required for update.")
                    
                self._validate_unit(unit, is_update=True, existing_unit_id=unit.id)
                
                # Check if unit exists
                existing = uow.units.get_by_id(unit.id)
                if not existing:
                    raise ValueError(f"Unit with ID {unit.id} not found.")
                
                # Check for name collision if name is being changed
                if existing.name != unit.name:
                    name_collision = uow.units.get_by_name(unit.name)
                    if name_collision and name_collision.id != unit.id:
                        raise ValueError(f"Another unit with name '{unit.name}' already exists.")
                
                # Update the unit
                updated_unit = uow.units.update(unit)
                uow.commit()
                
                self.logger.info(f"Unit updated successfully: {updated_unit.name} (ID: {updated_unit.id})")
                return updated_unit
                
            except Exception as e:
                self.logger.error(f"Error updating unit: {e}")
                uow.rollback()
                raise

    def delete_unit(self, unit_id: int) -> bool:
        """Delete a unit by its ID."""
        with unit_of_work() as uow:
            try:
                # Check if unit exists
                existing = uow.units.get_by_id(unit_id)
                if not existing:
                    raise ValueError(f"Unit with ID {unit_id} not found.")
                
                # Delete the unit
                success = uow.units.delete(unit_id)
                if success:
                    uow.commit()
                    self.logger.info(f"Unit deleted successfully: {existing.name} (ID: {unit_id})")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error deleting unit: {e}")
                uow.rollback()
                raise

    def search_units(self, query: str) -> List[Unit]:
        """Search for units based on name or abbreviation."""
        with unit_of_work() as uow:
            try:
                if not query or not query.strip():
                    return []
                return uow.units.search(query.strip())
            except Exception as e:
                self.logger.error(f"Error searching units with query '{query}': {e}")
                raise

    def toggle_unit_status(self, unit_id: int) -> Unit:
        """Toggle the active status of a unit."""
        with unit_of_work() as uow:
            try:
                unit = uow.units.get_by_id(unit_id)
                if not unit:
                    raise ValueError(f"Unit with ID {unit_id} not found.")
                
                # Toggle the status
                unit.is_active = not unit.is_active
                updated_unit = uow.units.update(unit)
                uow.commit()
                
                status = "activated" if updated_unit.is_active else "deactivated"
                self.logger.info(f"Unit {status}: {updated_unit.name} (ID: {unit_id})")
                return updated_unit
                
            except Exception as e:
                self.logger.error(f"Error toggling unit status: {e}")
                uow.rollback()
                raise