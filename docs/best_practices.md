# example-api - Best Practices

This file is read by PR-Agent to enforce team coding standards. Violations are flagged as "Organization best practice" suggestions.

Patterns that reference a custom primitive (`CustomException`, `@requires_permissions`,
`@with_transaction`) have a working reference implementation in
[`docs/custom_implementations/`](custom_implementations/README.md) — consult it before
reimplementing one of these from scratch.

---

## Pattern 1: Domain Layer Isolation

The domain layer must be pure Python with no framework dependencies. Code in `domain/` must never import from `infrastructure/` or `application/`.

Example code before:

```python
from src.pokemons.infrastructure.database.sql.models.pokemon_model import PokemonModelSQL

class Pokemon(BaseModel):
    name: str
```

Example code after:

```python
from pydantic import BaseModel

class Pokemon(BaseModel):
    name: str
```

---

## Pattern 2: SQL Model Conversion Methods

Every SQLAlchemy model must implement a `from_bo()` staticmethod and a `to_bo()` instance method to convert between the ORM layer and domain Business Objects. Never construct SQL models directly in use cases or routers.

Example code before:

```python
class PokemonModelSQL(BaseModelPgSQL, Base):
    __tablename__ = "pokemons"
    name = Column(String, nullable=False)
    status = Column(SQLEnum(PokemonStatusEnum), nullable=False)
```

Example code after:

```python
class PokemonModelSQL(BaseModelPgSQL, Base):
    __tablename__ = "pokemons"
    name = Column(String, nullable=False)
    status = Column(SQLEnum(PokemonStatusEnum), nullable=False)

    @staticmethod
    def from_bo(pokemon: Pokemon) -> "PokemonModelSQL":
        return PokemonModelSQL(
            name=pokemon.name,
            status=pokemon.status,
        )

    def to_bo(self) -> Pokemon:
        return Pokemon(
            id=self.id,
            name=self.name,
            status=self.status,
        )
```

---

## Pattern 3: Transaction Management

Use cases that modify data must use the `@with_transaction` decorator. This ensures proper session management and rollback on failure.

Example code before:

```python
@service()
class CreatePokemonUseCase(ICreatePokemonUseCase):
    @autowired
    def __init__(self, command_repo: IPokemonCommandRepository):
        self.command_repo = command_repo

    def execute(self, input_data: CreatePokemonInput) -> PokemonOutput:
        pokemon = Pokemon(name=input_data.name)
        return self.command_repo.save(pokemon)
```

Example code after:

```python
from src.core.infrastructure.database.sql.session_manager import with_transaction

@service()
class CreatePokemonUseCase(ICreatePokemonUseCase):
    @autowired
    def __init__(self, command_repo: IPokemonCommandRepository):
        self.command_repo = command_repo

    @with_transaction
    def execute(self, input_data: CreatePokemonInput) -> PokemonOutput:
        pokemon = Pokemon(name=input_data.name)
        return self.command_repo.save(pokemon)
```

---

## Pattern 4: Dependency Injection Decorators

All service classes must use `@service()` decorator. Constructor injection must use `@autowired`. Dependencies must be injected by interface, not by implementation.

Example code before:

```python
from src.pokemons.infrastructure.database.sql.repositories.pokemon_query_service_sql import PokemonQueryServiceSQL

class GetPokemonsUseCase:
    def __init__(self):
        self.query_service = PokemonQueryServiceSQL()
```

Example code after:

```python
from summer.inversion_of_control.dependencies import autowired, service
from src.pokemons.domain.repositories.i_pokemon_query_service import IPokemonQueryService

@service()
class GetPokemonsUseCase(IGetPokemonsUseCase):
    @autowired
    def __init__(self, query_service: IPokemonQueryService):
        self.query_service = query_service
```

---

## Pattern 5: Permission Guards on Endpoints

Every router endpoint must have the `@requires_permissions` decorator specifying the required action. No endpoint should be accessible without explicit permission checks.

Example code before:

```python
@router.get("/pokemons", response_model=list[PokemonOutput])
async def get_pokemons(self, request: Request):
    return self.use_case.execute()
```

Example code after:

```python
@router.get("/pokemons", response_model=list[PokemonOutput])
@requires_permissions(["pokemons:list"])
async def get_pokemons(self, request: Request):
    return self.use_case.execute()
```

---

## Pattern 6: Domain Exception Pattern

Domain exceptions must inherit from `CustomException` and set both `self.message` and `self.reason`. Do not raise generic Python exceptions from domain code.

Example code before:

```python
class PokemonNotFoundException(Exception):
    def __init__(self, pokemon_id: str):
        super().__init__(f"Pokemon {pokemon_id} not found")
```

Example code after:

```python
from custom_exceptions import CustomException

class PokemonNotFoundException(CustomException):
    def __init__(self, pokemon_id: str):
        self.message = f"Pokemon with ID {pokemon_id} not found."
        self.reason = "pokemonNotFound"
        super().__init__(self.message, self.reason)
```

---

## Pattern 7: Enum Pattern

All enums must inherit from `CustomEnum` (not Python's built-in `Enum` or `StrEnum`). This ensures consistent serialization and validation across the codebase.

Example code before:

```python
from enum import Enum

class PokemonStatusEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

Example code after:

```python
from src.core.domain.enum import CustomEnum

class PokemonStatusEnum(CustomEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
```

---

## Pattern 8: Repository Interface and Implementation

Repository interfaces live in the domain layer as ABCs. Implementations live in infrastructure and inherit from both the interface and `IDatabaseRepositorySQL`. Use `self.db` for session access.

Example code before:

```python
class PokemonQueryServiceSQL:
    def get_by_id(self, pokemon_id):
        from sqlalchemy import create_engine
        engine = create_engine("postgresql://...")
        # raw query
```

Example code after:

```python
from summer.inversion_of_control.dependencies import service
from src.core.infrastructure.database.sql.repositories.i_database_repository_sql import IDatabaseRepositorySQL
from src.pokemons.domain.repositories.i_pokemon_query_service import IPokemonQueryService

@service()
class PokemonQueryServiceSQL(IPokemonQueryService, IDatabaseRepositorySQL):
    def get_by_id(self, pokemon_id: uuid.UUID) -> Pokemon:
        entity = self.db.query(PokemonModelSQL).filter_by(id=pokemon_id).first()
        if not entity:
            raise PokemonNotFoundException(str(pokemon_id))
        return entity.to_bo()
```

---

## Pattern 9: Pydantic Serializers for API Input/Output

Router endpoints must use Pydantic serializers for request and response DTOs. Never return domain BOs directly from API endpoints. Output serializers must have a `from_bo()` staticmethod.

Example code before:

```python
@router.get("/pokemons/{pokemon_id}")
@requires_permissions(["pokemons:read"])
async def get_pokemon(self, request: Request, pokemon_id: uuid.UUID) -> Pokemon:
    return self.use_case.execute(pokemon_id)
```

Example code after:

```python
@router.get("/pokemons/{pokemon_id}", response_model=PokemonQueryModelOutput)
@requires_permissions(["pokemons:read"])
async def get_pokemon(self, request: Request, pokemon_id: uuid.UUID) -> PokemonQueryModelOutput:
    return self.use_case.execute(pokemon_id)
```

Where the serializer follows:

```python
class PokemonQueryModelOutput(BaseModel):
    id: uuid.UUID
    name: str
    status: str

    @staticmethod
    def from_bo(pokemon: Pokemon) -> "PokemonQueryModelOutput":
        return PokemonQueryModelOutput(
            id=pokemon.id,
            name=pokemon.name,
            status=pokemon.status,
        )
```

---

## Pattern 10: Test Factories

Test data factories must use Polyfactory's `ModelFactory` and provide a `build_and_save_to_db` classmethod that persists the entity and returns both the BO and the SQL model instance.

Example code before:

```python
def create_test_pokemon():
    return {"name": "Test", "status": "ACTIVE"}
```

Example code after:

```python
from polyfactory.factories.pydantic_factory import ModelFactory
from src.core.infrastructure.database.sql.session_manager import session_manager
from src.pokemons.domain.bo.pokemon import Pokemon
from src.pokemons.infrastructure.database.sql.models.pokemon_model import PokemonModelSQL

class PokemonBOFactory(ModelFactory[Pokemon]):
    @classmethod
    def build_and_save_to_db(cls, **kwargs) -> tuple[Pokemon, PokemonModelSQL]:
        entity_bo = cls.build(**kwargs)
        entity_instance = PokemonModelSQL.from_bo(entity_bo)
        with session_manager() as session:
            session.add(entity_instance)
            session.commit()
            entity_bo = entity_instance.to_bo()
        return entity_bo, entity_instance
```

---

## Pattern 11: API Test Method Structure

API tests must follow these conventions:
- Define `ENDPOINT` and `PERMISSION` constants at the top of the test file.
- Always include a `test_*_forbidden_wrong_permission` test to verify authorization.
- Use `mock_cognito_auth.generate_token(custom_claims={"custom:action": ...})` for authentication.
- Use `BOFactory.build_and_save_to_db(...)` to set up test data -- never insert raw dicts or use ORM directly in tests.
- Use fixtures from `conftest.py` for shared setup (e.g. `collaborator_with_spain_site`).
- Test names must be descriptive: `test_{endpoint}_{scenario}` (e.g. `test_history_returns_liquidations_ordered_by_date_desc`).
- Each test must assert the HTTP status code and validate the response body structure.
- Test edge cases: empty results, not found, filters, null fields.

Example code before:

```python
def test_get_pokemons(client):
    response = client.get("/pokemons")
    assert response.status_code == 200
```

Example code after:

```python
from fastapi.testclient import TestClient

from tests.pokemons.infrastructure.database.factories.pokemon import PokemonBOFactory

ENDPOINT = "/api/example-api/v1/pokemons"
PERMISSION = "pokemons:list"


def test_get_pokemons_forbidden_wrong_permission(api_client: TestClient, mock_cognito_auth):
    token = mock_cognito_auth.generate_token(custom_claims={"custom:action": '["wrong:permission"]'})

    response = api_client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json() == {"detail": f"Required permissions: {PERMISSION}"}


def test_get_pokemons_returns_empty_list(api_client: TestClient, mock_cognito_auth):
    token = mock_cognito_auth.generate_token(
        custom_claims={"custom:action": f'["{PERMISSION}"]'}
    )

    response = api_client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_get_pokemons_returns_pokemon_list(api_client: TestClient, mock_cognito_auth):
    pokemon, _ = PokemonBOFactory.build_and_save_to_db(name="Pikachu")

    token = mock_cognito_auth.generate_token(
        custom_claims={"custom:action": f'["{PERMISSION}"]'}
    )

    response = api_client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(pokemon.id)
    assert body[0]["name"] == "Pikachu"
```

---

## Pattern 12: Naming Conventions

Follow these naming conventions strictly:

| Type | Convention | Example |
|------|-----------|---------|
| Business Objects | PascalCase | `Pokemon`, `CompanyLiquidation` |
| SQL Models | PascalCase + `ModelSQL` | `PokemonModelSQL` |
| Repository Interfaces | `I` prefix + PascalCase | `IPokemonQueryService` |
| Repository Implementations | PascalCase + `SQL` suffix | `PokemonQueryServiceSQL` |
| Use Case Interfaces | `I` prefix + PascalCase + `UseCase` | `IGetPokemonsUseCase` |
| Enums | PascalCase + `Enum` | `PokemonStatusEnum` |
| Exceptions | PascalCase + `Exception` | `PokemonNotFoundException` |
| Test Factories | PascalCase + `BOFactory` | `PokemonBOFactory` |
| DB Tables | plural, snake_case | `pokemons`, `company_liquidations` |
| Foreign keys | `{referenced_table_singular}_id` | `company_id`, `site_id` |
