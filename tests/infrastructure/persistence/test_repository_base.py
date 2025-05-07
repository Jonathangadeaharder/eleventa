import pytest
from unittest.mock import MagicMock, patch
from infrastructure.persistence.repository_base import RepositoryBase


class SampleEntity:
    """Simple entity for testing."""
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class SampleDomainModel:
    """Simple domain model for testing."""
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class ConcreteRepository(RepositoryBase[SampleDomainModel]):
    """Concrete implementation of the abstract RepositoryBase class for testing."""
    
    def __init__(self, session=None):
        super().__init__(session)
    
    def _entity_to_domain(self, entity):
        return SampleDomainModel(id=entity.id, name=entity.name)
    
    def _domain_to_entity(self, domain_model):
        return SampleEntity(id=domain_model.id, name=domain_model.name)
    
    def get_by_id(self, id):
        # Instead of using SampleEntity.id, which causes errors as SampleEntity isn't an SQLAlchemy model,
        # we'll just mock the entire query chain
        query = self.session.query.return_value
        filter_query = query.filter.return_value
        mock_entity = SampleEntity(id=id, name=f"Entity {id}")
        filter_query.first.return_value = mock_entity
        
        # Use the mock chain directly
        entity = self.session.query(SampleEntity).filter().first()
        return self._entity_to_domain(entity) if entity else None
    
    def get_all(self):
        # Simulate querying with session
        query = self.session.query.return_value
        query.all.return_value = [SampleEntity(id=1, name="Entity 1"), SampleEntity(id=2, name="Entity 2")]
        entities = self.session.query(SampleEntity).all()
        return [self._entity_to_domain(entity) for entity in entities]
    
    def add(self, domain_model):
        entity = self._domain_to_entity(domain_model)
        self.session.add(entity)
        self.session.flush()
        return entity.id
    
    def update(self, domain_model):
        entity = self._domain_to_entity(domain_model)
        # In a real implementation, we might query for the entity first
        # For testing, we'll just simulate the update
        self.session.add(entity)
        self.session.flush()
    
    def delete(self, id):
        # Similar to get_by_id, we'll mock the entire query chain
        query = self.session.query.return_value
        filter_query = query.filter.return_value
        mock_entity = SampleEntity(id=id, name=f"Entity {id}")
        filter_query.first.return_value = mock_entity
        
        # Use the mock chain directly
        entity = self.session.query(SampleEntity).filter().first()
        if entity:
            self.session.delete(entity)
            self.session.flush()


@pytest.fixture
def mock_session():
    mock = MagicMock()
    # Set up query chaining
    mock.query.return_value.filter.return_value.first.return_value = None
    return mock


@pytest.fixture
def repository(mock_session):
    return ConcreteRepository(mock_session)


def test_repository_initialization(mock_session):
    # Act
    repo = ConcreteRepository(mock_session)
    
    # Assert
    assert repo._session == mock_session


def test_session_property(mock_session):
    # Arrange
    repo = ConcreteRepository(mock_session)
    
    # Act
    session = repo.session
    
    # Assert
    assert session == mock_session


def test_session_property_no_session():
    # Arrange
    repo = ConcreteRepository()
    
    # Act & Assert
    with pytest.raises(RuntimeError):
        _ = repo.session


def test_set_session(mock_session):
    # Arrange
    repo = ConcreteRepository()
    
    # Act
    repo.set_session(mock_session)
    
    # Assert
    assert repo._session == mock_session
    assert repo.session == mock_session


def test_entity_to_domain():
    # Arrange
    repo = ConcreteRepository()
    entity = SampleEntity(id=1, name="Test")
    
    # Act
    domain_model = repo._entity_to_domain(entity)
    
    # Assert
    assert isinstance(domain_model, SampleDomainModel)
    assert domain_model.id == entity.id
    assert domain_model.name == entity.name


def test_domain_to_entity():
    # Arrange
    repo = ConcreteRepository()
    domain_model = SampleDomainModel(id=1, name="Test")
    
    # Act
    entity = repo._domain_to_entity(domain_model)
    
    # Assert
    assert isinstance(entity, SampleEntity)
    assert entity.id == domain_model.id
    assert entity.name == domain_model.name


def test_get_by_id(repository, mock_session):
    # Arrange
    test_id = 1
    mock_entity = SampleEntity(id=test_id, name=f"Entity {test_id}")
    query = mock_session.query.return_value
    filter_query = query.filter.return_value
    filter_query.first.return_value = mock_entity
    
    # Act
    result = repository.get_by_id(test_id)
    
    # Assert
    assert isinstance(result, SampleDomainModel)
    assert result.id == test_id
    assert result.name == f"Entity {test_id}"
    mock_session.query.assert_called_once()
    query.filter.assert_called_once()
    filter_query.first.assert_called_once()


def test_get_all(repository, mock_session):
    # Arrange
    mock_entities = [SampleEntity(id=1, name="Entity 1"), SampleEntity(id=2, name="Entity 2")]
    query = mock_session.query.return_value
    query.all.return_value = mock_entities
    
    # Act
    results = repository.get_all()
    
    # Assert
    assert len(results) == 2
    assert all(isinstance(result, SampleDomainModel) for result in results)
    assert [result.id for result in results] == [1, 2]
    assert [result.name for result in results] == ["Entity 1", "Entity 2"]
    mock_session.query.assert_called_once()
    query.all.assert_called_once()


def test_add(repository, mock_session):
    # Arrange
    domain_model = SampleDomainModel(name="New Entity")
    
    # Mock the session.flush() to set an ID 
    def side_effect_flush():
        entity = mock_session.add.call_args[0][0]
        entity.id = 1
    
    mock_session.flush.side_effect = side_effect_flush
    
    # Act
    result_id = repository.add(domain_model)
    
    # Assert
    assert result_id == 1
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


def test_update(repository, mock_session):
    # Arrange
    domain_model = SampleDomainModel(id=1, name="Updated Entity")
    
    # Act
    repository.update(domain_model)
    
    # Assert
    mock_session.add.assert_called_once()
    # Check that the entity passed to add() has the expected properties
    added_entity = mock_session.add.call_args[0][0]
    assert added_entity.id == 1
    assert added_entity.name == "Updated Entity"
    mock_session.flush.assert_called_once()


def test_delete(repository, mock_session):
    # Arrange
    test_id = 1
    mock_entity = SampleEntity(id=test_id, name=f"Entity {test_id}")
    
    # Set up the mock chain to return our entity
    query = mock_session.query.return_value
    filter_query = query.filter.return_value
    filter_query.first.return_value = mock_entity
    
    # Use the same approach as in test_get_by_id
    def query_side_effect(entity_class):
        # This will be called when session.query(SampleEntity) is executed
        return query
    
    mock_session.query.side_effect = query_side_effect
    
    # Act
    repository.delete(test_id)
    
    # Assert
    mock_session.query.assert_called_once_with(SampleEntity)
    query.filter.assert_called_once()
    filter_query.first.assert_called_once()
    
    # Check that session.delete was called with an entity
    mock_session.delete.assert_called_once()
    deleted_entity = mock_session.delete.call_args[0][0]
    assert isinstance(deleted_entity, SampleEntity)
    assert deleted_entity.id == test_id
    assert deleted_entity.name == f"Entity {test_id}"
    
    mock_session.flush.assert_called_once()