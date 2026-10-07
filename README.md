# Fatowin (GitHub Pages version)

Modified Fatowin landing page:

- Font changed to **Proxima Nova**
- Working **Login / Register** by Username + Password
- Users are stored in the browser (`localStorage`)

## How to publish on GitHub Pages

1. Create a new repository on GitHub (or use existing).
2. Upload **only** the file `index.html` (and this README if you want).
3. Go to repository **Settings → Pages**.
4. Under **Source** choose:
   - Branch: `main` (or `master`)
   - Folder: `/ (root)`
5. Save. Wait 1–2 minutes.
6. Your site will be available at:

   `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

## How auth works

- Register / Login by **Username + Password**
- Data is saved in the visitor’s browser (`localStorage`)
- On the same browser the account will remain after page reload
- On another device / browser the account will **not** be available (this is normal for pure static GitHub Pages)

## Notes

- Minimum username: 3 characters
- Minimum password: 4 characters
- New users get $1000 play-money balance
