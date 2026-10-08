# Architecture Skill

## Purpose

Apply DDD and Clean/Hexagonal Architecture pragmatically.

## Rules

- Keep domain logic independent of frameworks and infrastructure.
- Define interfaces at the boundary where inversion of control is useful.
- Keep application services focused on use-case orchestration.
- Keep infrastructure adapters replaceable.
- Avoid premature abstractions.
- Prefer explicit dependencies over service locators and hidden globals.
- Record significant architectural decisions and their rationale.

## Preferred structure

```text
src/
  <module>/
    domain/
    application/
    infrastructure/
```

Interfaces may live in domain/application when they express contracts required by those layers.

## Review checklist

- Is dependency direction correct?
- Is business logic in the domain/application layer rather than infrastructure?
- Are external concerns isolated?
- Is the abstraction justified by a real boundary?
- Can the relevant component be tested without external infrastructure?
