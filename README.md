# Fatowin (modified) — Proxima Nova + Auth

Modified version of the Fatowin landing page:

- Full font changed to **Proxima Nova**
- Working **Login / Register** by Username + Password
- Users are stored on the server in `users.json`

## Files

| File        | Description                                      |
|-------------|--------------------------------------------------|
| `index.html`| Modified landing page (Proxima Nova + auth UI)   |
| `server.py` | Python HTTP server with register/login API       |
| `users.json`| Database of registered users (created automatically) |

## How to run

```bash
python3 server.py
```

Open in browser: **http://localhost:8080**

### API endpoints

- `POST /api/register` — `{ "username": "...", "password": "..." }`
- `POST /api/login`    — `{ "username": "...", "password": "..." }`
- `GET  /api/me`       — requires `Authorization: Bearer <token>`
- `POST /api/logout`   — requires `Authorization: Bearer <token>`

## Notes

- Minimum username length: 3 characters
- Minimum password length: 4 characters
- Passwords are stored as SHA-256 + salt
- New users receive $1000 play-money balance
- Session token is saved in browser `localStorage`
