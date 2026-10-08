# Naming and Project Structure Skill (EXAMPLE — adapt per project's stack)

> The tables below show one concrete, worked convention (Python, hexagonal/DDD, SQLAlchemy-backed
> repositories) so a new project has a real example to adapt rather than an abstract rulebook. Once
> a project's own convention is decided, rewrite this file to match that project's actual stack and
> treat it as the binding rule from then on — do not leave two competing conventions active.

## Purpose

Keep modules, classes, use cases, repositories, tests and database objects consistent within one
project.

## Files and directories (example)

| Type | Convention | Example |
|---|---|---|
| Modules/directories | `snake_case`, plural when representing a module/collection | `pokemons/` |
| Source files | `snake_case` | `pokemon_model.py` |
| Test files | `test_` prefix | `test_pokemons_router.py` |
| Use-case directories | `snake_case` with a verb | `get_pokemons_use_case/` |
| CLI/entry-point files | `{command_name}_cli.py` (never `main.py`, `cli.py`, or another generic name) | `run_bootstrap_cli.py` |

## Classes (example)

| Type | Convention | Example |
|---|---|---|
| Business Objects | PascalCase | `Pokemon` |
| Persistence models | PascalCase + `ModelSQL`/framework suffix | `PokemonModelSQL` |
| Repository interfaces | `I` + PascalCase | `IPokemonQueryService` |
| Use Cases | PascalCase + `UseCase` | `GetPokemonUseCase` |
| Enums | PascalCase + `Enum` | `PokemonStatusEnum` |
| Exceptions | PascalCase + `Exception` | `PokemonNotFoundException` |
| Test factories | PascalCase + `BOFactory` | `PokemonBOFactory` |

## Use-case action methods

A use case's public action method — declared on its interface and implemented by the concrete
class — should be named after the use case itself, not a generic verb.

Rule: take the use case class name, drop the trailing `UseCase` suffix, and convert the remainder
to `snake_case`. The interface and the implementation should use the identical method name. Avoid
generic names like `execute`, `run`, `call`, `handle` — the method name should let a reader
identify the use case from a call site alone.

| Use Case class | Action method |
|---|---|
| `GetPokemonUseCase` | `get_pokemon()` |
| `RunBootstrapUseCase` | `run_bootstrap()` |

## Application structure (example — hexagonal/DDD)

```text
src/{module_name}/
├── application/
│   └── {use_case_name}/
│       ├── __init__.py
│       ├── i_{use_case_name}.py
│       ├── {use_case_name}.py
│       └── serializers/
├── domain/
│   ├── bo/
│   ├── enums/
│   ├── exceptions/
│   └── repositories/
└── infrastructure/
    ├── api/
    │   └── v1/
    └── database/
        └── sql/
            ├── models/
            └── repositories/
```

## Repository names (example, SQL-backed)

- Query contract: `i_{entity}_query_repository.py` -> `I{Entity}QueryRepository`
- Command contract: `i_{entity}_command_repository.py` -> `I{Entity}CommandRepository`
- Concrete implementations named after the actual persistence technology, e.g.
  `sql_alchemy_{entity}_query_repository.py` -> `SqlAlchemy{Entity}QueryRepository`, or
  `in_memory_{entity}_query_repository.py` -> `InMemory{Entity}QueryRepository`.

Both sides are named `*Repository` — a query contract is a repository with only read methods, not
a different kind of object.

Not every entity needs both sides: introduce a command interface only when a real write use case
exists for that entity.

## Database naming (example, relational)

- Tables: plural `snake_case`: `pokemons`
- Association tables: `{table1}_{table2}_association`
- Foreign keys: singular referenced table + `_id`: `pokemon_id`
- Columns: `snake_case`: `created_at`

## Rules

Naming is part of the architecture. Do not invent a competing naming convention for a new feature
within the same project.

When an existing repository contains an established convention, follow it unless requirements or
architecture explicitly change it.
