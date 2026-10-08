# Dependency Injection Skill (EXAMPLE — swap per project)

> This skill is a worked example, not a default. Only keep a DI skill in a new project if that
> project actually uses a DI/IoC framework. Replace `python-summer-boot` below with whatever the
> project has chosen (or delete this skill entirely for projects that use plain constructor
> wiring without a container).

## Purpose

Pick one dependency-injection mechanism for the project and use it consistently. Do not let two
DI approaches coexist.

## Registration

Concrete implementations that are managed by the container should be registered explicitly
(container decorator, factory function, or explicit wiring module — whatever the chosen framework
provides). Example using `python-summer-boot`:

```python
from summer.inversion_of_control.dependencies import service

from src.pokemons.domain.repositories.i_pokemon_query_service import IPokemonQueryService


@service()
class PokemonQueryService(IPokemonQueryService):
    ...
```

## Injection

Dependencies should be injected through constructor injection, using the chosen framework's
mechanism. Example:

```python
from summer.inversion_of_control.dependencies import autowired

from src.pokemons.domain.repositories.i_pokemon_query_service import IPokemonQueryService


class GetPokemonUseCase:
    @autowired
    def __init__(self, pokemon_query_service: IPokemonQueryService):
        self.pokemon_query_service = pokemon_query_service
```

## Application bootstrap

The chosen framework's service discovery/registration must run exactly once, before dependency
injection is used. Example:

```python
from summer.inversion_of_control.service_locator import (
    discover_services,
    get_executable_parent_path,
)

import your_package


def setup() -> None:
    discovery_root = get_executable_parent_path(your_package.__file__)
    discover_services(discovery_root)
```

Compute the discovery root from the runtime package's own `__file__`, not from `os.getcwd()`.
Scoping discovery to the package's own directory is precise and deterministic; scoping it to the
current working directory scans far too broadly (it can include `tests/`, `.venv/`, `.git/`, etc.)
and its result depends on where the command happens to be invoked from.

## Interfaces

Repositories and use cases should expose explicit interfaces (e.g. `ABC` in Python) where an
abstraction is required by the architecture, not by habit.

```python
from abc import ABC, abstractmethod


class IPokemonQueryService(ABC):
    @abstractmethod
    def get_by_id(self, pokemon_id: str):
        raise NotImplementedError
```

## Transaction handling

For use cases that modify persistent state, use the project's transaction mechanism at the
application/use-case boundary, not inside domain objects. Example:

```python
@with_transaction
def execute(...):
    ...
```

## Rules

- Do not instantiate container-managed services manually when injection is available.
- Do not create a second DI mechanism.
- Do not use service locators inside business logic.
- Keep dependency wiring at application/bootstrap boundaries.
- Use constructor injection.
- Depend on interfaces where the architectural boundary requires inversion.
- Every container-managed service must have a clear reason to be container-managed.

## Review checklist

- Is the implementation registered with the project's chosen mechanism?
- Is injection performed through constructor injection?
- Is the dependency typed against the appropriate interface?
- Is the DI framework initialized before injection is used?
- Is transaction handling at the use-case boundary where required?
- Has a second DI framework or hidden service locator been introduced?
