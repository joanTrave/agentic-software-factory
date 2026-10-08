# Custom implementations

Reference implementations of the custom primitives [`../best_practices.md`](../best_practices.md)
assumes exist, so its code examples refer to something concrete rather than an unimplemented
convention.

| File | Backs pattern | Provides |
|---|---|---|
| `custom_exception.py` | Pattern 6 (Domain Exception Pattern) | `CustomException`, `CustomNotFoundException`, a FastAPI exception handler |
| `requires_permissions.py` | Pattern 5 (Permission Guards on Endpoints) | `@requires_permissions([...])` |
| `with_transaction.py` | Pattern 3 (Transaction Management) | `@with_transaction`, `session_manager()`, `configure_session_factory()` |

These are starting points for a new project, not drop-in production code — wire
`configure_session_factory()` to the project's real engine/sessionmaker, and replace
`requires_permissions.py`'s unverified-JWT read with the project's actual auth/token
verification before relying on it for real authorization.
