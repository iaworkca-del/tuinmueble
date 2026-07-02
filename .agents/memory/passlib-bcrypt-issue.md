---
name: Passlib + bcrypt incompatibility
description: passlib's CryptContext(schemes=["bcrypt"]) can fail at import/startup time with newer bcrypt versions installed via Replit's package manager.
---

Using `passlib.context.CryptContext(schemes=["bcrypt"])` can raise `AttributeError: module 'bcrypt' has no attribute '__about__'` followed by `ValueError: password cannot be longer than 72 bytes...` during passlib's internal backend self-test, crashing the app at startup (e.g. when hashing a seed/admin password at module import time).

**Why:** passlib 1.7.x reads `bcrypt.__about__.__version__` to detect the backend version; newer `bcrypt` package releases removed that attribute, which breaks passlib's internal wrap-bug detection routine before any real hashing happens.

**How to apply:** Skip passlib for bcrypt hashing. Use the `bcrypt` package directly:
```python
import bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")
def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
```
Truncate to 72 bytes manually since bcrypt has a hard length limit. This avoids the passlib compatibility layer entirely.
