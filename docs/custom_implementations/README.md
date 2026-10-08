# Custom implementations

Reference implementations of the custom primitives [`../best_practices.md`](../best_practices.md)
assumes exist, so its code examples refer to something concrete rather than an unimplemented
convention.

| File | Backs pattern | Provides |
|---|---|---|
| `custom_exception.py` | Pattern 6 (Domain Exception Pattern) | `CustomException`, `CustomNotFoundException`, a FastAPI exception handler |
| `requires_permissions.py` | Pattern 5 (Permission Guards on Endpoints) | `@requires_permissions([...])` |
| `with_transaction.py` | Pattern 3 (Transaction Management) | `@with_transaction`, `session_manager()`, `get_read_session()`, `configure_session_factory()` |

These are starting points for a new project, not drop-in production code — wire
`configure_session_factory()` to the project's real engine/sessionmaker, and replace
`requires_permissions.py`'s unverified-JWT read with the project's actual auth/token
verification before relying on it for real authorization.

## Where each primitive was wired in (`constitution` task)

| File here | Wired to | Notes |
|---|---|---|
| `custom_exception.py` | `src/core/domain/exceptions/custom_exception.py` (domain, no framework import) + `src/core/infrastructure/api/exception_handlers.py` (the FastAPI handler, split out — see the architecture gate's Decision D4) | Registered once in `src/app.py` via `app.add_exception_handler(CustomException, custom_exception_handler)`. |
| `with_transaction.py` | `src/core/infrastructure/database/sql/session_manager.py`, verbatim (including `get_read_session()`, which backs `IDatabaseRepositorySQL.db`) | `configure_session_factory()` is called once from `src/core/infrastructure/bootstrap.py` with the engine/sessionmaker built in `src/core/infrastructure/database/sql/engine.py`. |
| `requires_permissions.py` | `src/core/infrastructure/api/security/requires_permissions.py` | Its unverified-JWT read is replaced with real Cognito JWKS verification when `COGNITO_REGION`/`COGNITO_USER_POOL_ID`/`COGNITO_CLIENT_ID` are set (required by `Settings` in `staging`/`production`); `local`/`test` fall back to the original unverified decode so `mock_cognito_auth`'s locally-signed tokens keep working. |

No business bounded context (`src/<module>/`) exists yet in this repository — the first module to
use `@requires_permissions` on a real endpoint should confirm the Cognito wiring above against a
real user pool before relying on it.
