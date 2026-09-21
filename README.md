# adadeowebsite

Public site for adadeo.ie (GitHub Pages via the `CNAME` file).

## Structure

| File | Purpose |
|---|---|
| `index.html` | Corporate home page |
| `qa.html` | QA consulting page |
| `secye.html` | Secye app + legal documents — **English** (`#privacy`, `#terms`, `#disclaimer`, `#delete-account`, `#support`) |
| `secye-tr.html` | Same documents — **Türkçe / KVKK** |
| `secye-pl.html` | Same documents — **Polski / RODO** |
| `lang.js` | Language auto-serve + switcher for the three legal pages |

Deep links never break: every language page uses the same five anchor names, so
`https://adadeo.ie/secye.html#privacy` resolves to the same section in the
visitor's language.

## Adding a language

1. Copy `secye.html` → `secye-XX.html`, translate, and keep the five anchors.
2. Set `<body data-page-lang="XX">` and list all languages in the header
   `lang-switch`.
3. Add one entry to `PAGES` (and `LABELS`) in `lang.js`.
4. Add the `LEGAL_PAGE_URL_XX` config + an entry in the `pages` map in the app
   backend (`app/core/config.py`, `routers/legal.py`) so `/api/v1/legal/info`
   publishes it.