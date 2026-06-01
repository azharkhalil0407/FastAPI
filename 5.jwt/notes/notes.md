# JWT Authentication 

---

## What is JWT?

JWT (JSON Web Token) is a **stateless authentication token** — a string with three parts separated by dots:

| Part | Content |
|------|---------|
| **Header** | Algorithm used (e.g., `HS256`) |
| **Payload** | Actual data (email, expiry, etc.) |
| **Signature** | Header + Payload signed with `SECRET_KEY` |

**Format:** `header.payload.signature`

**Example:**
```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QGdtYWlsLmNvbSJ9.4bVkBs0g6ZqMfH1mLkOjQw
```

---

## Why JWT? (Problem it Solves)

- HTTP is **stateless** — server forgets everything after each request.
- Without JWT, server wouldn't recognize a logged-in user on the next request.
- **Old solution (sessions):** Server stores session in memory/DB → DB hit on every request → doesn't scale.
- **JWT solution:** Server issues token → user sends token with every request → server verifies **without** a DB hit.

---

## JWT Internal Structure

| Part | Content | Encoding |
|------|---------|----------|
| Header | `{"alg": "HS256", "typ": "JWT"}` | Base64 |
| Payload | `{"sub": "user@gmail.com", "exp": 1735689600}` | Base64 |
| Signature | `HMAC-SHA256(header + "." + payload, SECRET_KEY)` | Base64 |

> **Critical:** Payload is Base64 encoded, NOT encrypted. Anyone can decode it.  
> Never store sensitive data (passwords, credit cards) in JWT.

---

## SECRET_KEY

- A long random string known **only to your server**.
- Used to **sign** the token on creation.
- Used to **verify** the signature on decoding.
- Stored in `.env` file.
- If stolen, attackers can create fake tokens.

---

## Key FastAPI Utilities

### `OAuth2PasswordRequestForm`
- Parses **form data** (not JSON).
- Expects format: `username=email&password=password`
- Field name is `username` but you pass email (OAuth2 standard).
- Use `form_data.username` for email, `form_data.password` for password.

### `OAuth2PasswordBearer`
- Extracts token from the `Authorization` header.
- Expects format: `Authorization: Bearer <token>`
- Usage:
  ```python
  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
  token: str = Depends(oauth2_scheme)
  ```
- If header is missing or malformed → auto returns `401`.

---

## Complete Login Flow (9 Steps)

### Step 1 — User Sends Login Request
- Endpoint: `POST /users/login`
- Format: Form data → `username=test@gmail.com&password=test123`

### Step 2 — Server Finds User in Database
```python
user = get_user_by_email(form_data.username, db)
```
- No user found → `401 Unauthorized`

### Step 3 — Server Verifies Password
```python
verify_password(form_data.password, user.password)
```
- Wrong password → `401 Unauthorized`

### Step 4 — Server Creates JWT Token
```python
token = create_access_token({"sub": user.email})
```
- `sub` = subject (JWT standard for user identifier).
- Expiry added automatically (30 minutes).

### Step 5 — Server Returns Token
```python
return {"access_token": token, "token_type": "bearer"}
```

### Step 6 — Client Sends Token on Every Request
- Header: `Authorization: Bearer <token>`

### Step 7 — Server Verifies Token
```python
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```
- Expired or tampered token → `JWTError` → `401 Unauthorized`

### Step 8 — Server Extracts Email from Payload
```python
email = payload.get("sub")  # "test@gmail.com"
```

### Step 9 — Server Returns User
```python
return get_user_by_email(email, db)
```

---

## Token Expiry — Why It Matters

- Tokens expire (typically 15-30 minutes).
- If a token is stolen, it only works for a limited time.
- Added in `create_access_token`:

```python
expire = datetime.utcnow() + timedelta(minutes=30)
to_encode.update({"exp": expire})
```

---

## Code Summary — Key Functions

### `utils.py` — `create_access_token`
```python
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, setting.SECRET_KEY, algorithm="HS256")
```

### `utils.py` — `get_current_user`
```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, setting.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return get_user_by_email(email, db)
```

### `routers/users.py` — Login Endpoint
```python
@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(form_data.username, db)
    if not user:
        raise HTTPException(status_code=401)
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401)
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
```

### `routers/users.py` — Protected Endpoint
```python
@router.get('/me', response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user
```

---

## Common Mistakes

| Mistake | Why It's Wrong |
|---------|---------------|
| Storing sensitive data in payload | Payload is Base64 — anyone can decode it |
| Weak `SECRET_KEY` | Use 32+ char random string |
| No expiry on token | Stolen tokens work forever |
| Using dot notation on payload (`payload.sub`) | Payload is a dict — use `payload.get("sub")` |
| Forgetting to import `get_db` | Causes circular imports — move to `dependencies.py` |
| Sending JSON to `OAuth2PasswordRequestForm` | It only reads form data |

---

## Memory Trick — REGVT → GETU

**Login (5 steps):**
1. **R**equest (form data)
2. **E**xists (check DB)
3. **G**o verify (password check)
4. **V**erify passed → create token with `{"sub": email}`
5. **T**oken returned

**Protected Request (5 steps):**
1. **G**et request with `Authorization: Bearer`
2. **E**xtract token (`OAuth2PasswordBearer`)
3. **T**oken verify (`jwt.decode`)
4. **U**ser email (`payload.get("sub")`)
5. User returned

---

## Project File Structure 

```
backend/
├── app/
│   ├── dependencies.py      # get_db() moved here to avoid circular import
│   ├── utils.py             # hash, verify, create_token, get_current_user
│   ├── database.py          # engine, sessionLocal
│   ├── routers/
│   │   └── users.py         # register, login, me endpoints
│   ├── crud/
│   │   └── users.py         # get_user_by_email, create_user
│   ├── schemas/
│   │   └── users.py         # UserCreate, UserResponse
│   └── models/
│       └── users.py         # SQLAlchemy User model
├── notes/
│   └── notes.md             # project notes
├── config.py                # settings with SECRET_KEY
├── main.py                  # FastAPI app, include router
├── requirements.txt         # project dependencies
└── products.db              # SQLite database file
```