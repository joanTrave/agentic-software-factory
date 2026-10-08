# translations

Locale message catalogues: `<locale>/LC_MESSAGES/*.po|.mo`.

Only user-facing strings are translatable — notably `CustomException.message`
(`src/core/domain/exceptions/custom_exception.py`). `reason` codes are **never** translated, since
clients switch on them programmatically.

Empty until the first module needs a translated string.
