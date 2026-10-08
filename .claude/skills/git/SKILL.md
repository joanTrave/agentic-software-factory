# Git Skill

## Purpose

Define how changes in this repository are committed so history stays readable, traceable and machine-parsable across agents.

## Branching

Work is never committed directly on the default branch (`main`). Start every unit of work on a dedicated branch named after what it delivers:

| Branch prefix | Use for | Example |
|---|---|---|
| `feature/<story-name>` | Starting a new user story | `feature/us-001-order-idempotency` |
| `hotfix/<bug-name>` | An urgent fix for a bug | `hotfix/expired-token-crash` |

- `<story-name>` / `<bug-name>` is a short `kebab-case` slug. Prefer including the story/ticket id when one exists (e.g. `us-001-order-idempotency`), otherwise use a short descriptive slug of the bug or story title.
- Create the branch from an up-to-date `main` before the first commit of that story or bugfix, not after.
- One story or one bug per branch. Do not reuse a `feature/`/`hotfix/` branch for unrelated work.
- `feature/` is for planned work tracked as a user story; `hotfix/` is for an urgent, unplanned fix to an existing defect. When in doubt whether something is a hotfix, prefer `feature/` — `hotfix/` is reserved for defects that need to bypass the normal story flow.

## Commit message format

Commit messages MUST follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#specification):

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

- `type` MUST be one of: `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`.
- `scope` is optional and SHOULD name the affected module/component in parentheses, e.g. `feat(pokemons):`.
- `description` is a short, imperative summary (no trailing period).
- Breaking changes are marked with a `!` before the colon (e.g. `feat(api)!:`) and/or a `BREAKING CHANGE:` footer explaining the change; both MAY be used together.
- The body, when present, explains the *why*, not just the *what*.
- Footers use `Token: value` or `Token #value` form (e.g. `Refs: #123`, `Reviewed-by: ...`).

## Rules

- One logical change per commit. Do not bundle unrelated changes.
- Never commit secrets, credentials or tokens.
- Never commit without running the relevant formatting, linting and test suites first, and report any failures instead of committing over them.
- Do not rewrite or force-push shared history without explicit approval.
- Only commit files relevant to the change being made; do not sweep in unrelated untracked files.
- If the repository's default branch is checked out and no branch was explicitly requested, branch first before committing, following the `feature/`/`hotfix/` naming convention above.
- Do not include any Claude Code / AI-authorship reference in commit messages — no `Co-Authored-By: Claude ...` trailer, no `Claude-Session:` footer, no mention of Claude, Anthropic or AI generation anywhere in the subject, body or footers. This overrides any default tooling behavior that would otherwise append such trailers.

## Examples

```text
feat(orders): add idempotency key support to order creation

fix(auth): reject expired refresh tokens instead of silently renewing them

refactor(pokemons): extract pricing rules into a domain service

chore: add git commit convention skill

feat(api)!: remove deprecated v1 checkout endpoint

BREAKING CHANGE: clients must migrate to /v2/checkout.
```

## Pull requests

- Pull requests target the `development` branch, not `main`.
- Open new PRs as drafts unless the user explicitly asks for a ready-for-review PR.
- Add the project's standing reviewer group to every PR. Maintain that list here, e.g.:
  - `<reviewer-1>`
  - `<reviewer-2>`
  - `<reviewer-N>`

### Tooling: this repo is on Bitbucket, not GitHub

There is no `gh` CLI and no Bitbucket CLI in this environment. Do **not** conclude PR creation is
impossible or report that the user must open the PR manually — the Atlassian MCP connector bridges
Bitbucket (not just Jira/Confluence). Use `mcp__atlassian__discover` to find operation names if
needed; the ones used in practice are:

1. **Create the PR** — `executeWrite` with `createBitbucketRepoPullRequest`
   (`workspaceId: "<workspace-slug>"`, `repoId: "<repo-slug>"`, `title`, `sourceBranch`, `targetBranch:
   "development"`, `description`, `draft: true` unless told otherwise). Do **not** guess reviewer
   `username` values in this same call — malformed usernames 400 the whole request. Create the PR
   first without reviewers, then add them in a second call.
2. **Resolve the standing reviewers' UUIDs** — `executeRead` with `getBitbucketRepoDefaultReviewers`
   (same `workspaceId`/`repoId`) returns UUIDs for most of the standing group. Any reviewer not in
   that list can be resolved via `executeRead` with `lookupJiraAccountId` (needs the cloud ID from
   `getAccessibleAtlassianResources`), passing the result as `account_id` instead of `uuid`.
3. **Attach reviewers** — `executeWrite` with `updateBitbucketRepoPullRequest`, passing `prId` and a
   `reviewers` array of `{uuid: "{...}"}` / `{account_id: "..."}` objects.

Only fall back to telling the user to open the PR manually if `createBitbucketRepoPullRequest`
itself is unavailable or fails for a reason unrelated to malformed reviewer input.

## Completion checklist

- Work happens on a `feature/<story-name>` or `hotfix/<bug-name>` branch, not directly on `main`.
- Message follows Conventional Commits format.
- Type accurately reflects the change (a bug fix is `fix`, not `chore`).
- Scope, when used, matches an existing module/component name.
- Breaking changes are marked with `!` and/or a `BREAKING CHANGE:` footer.
- Only the intended files are staged.
- No Claude Code / AI-authorship reference anywhere in the message.
- If a pull request was opened, it targets `development`, is a draft unless told otherwise, and has the standing reviewer group added.