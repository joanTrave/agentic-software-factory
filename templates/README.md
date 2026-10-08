# templates

Jinja2 templates for generated artifacts (emails, PDFs, ...). No module reads this directory
directly — render through a shared helper in `src/core/infrastructure/templates/` (added when the
first module needs one) rather than loading template files ad hoc.

Empty until the first module needs a generated document.
