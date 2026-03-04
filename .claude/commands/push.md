# Push to GitHub

Check everything, commit any changes, and push to origin/main.

## Steps

### 1. Check git status
Run `git status` and `git diff --stat` to see all changes (staged, unstaged, untracked).

- If there is **nothing to commit and nothing to push**, tell the user and stop.
- If there are changes, continue.

### 2. Frontend build check
If any files under `frontend/` were modified, verify the frontend still builds cleanly:

```bash
cd frontend && npm run build
```

- If the build **fails**, stop and show the error. Do not commit.
- If it passes, continue. (You do not need to commit the `frontend/dist/` output — it is built inside Docker.)

### 3. Review the diff
Run `git diff HEAD` (or `git diff` if nothing is staged yet) and summarize the changes for the user in 3–5 bullet points. Be specific: which files changed and what kind of change (new feature, fix, refactor, etc.).

### 4. Draft a commit message
Write a conventional-commit style message:
- Subject line: `type(scope): short description` (max 72 chars)
- Types: `feat`, `fix`, `refactor`, `style`, `chore`, `docs`
- Body (optional): 1–3 sentences explaining *why*, not *what*

Present the message to the user and ask for approval or edits before committing.

### 5. Stage and commit
Once the user approves the message:

```bash
git add -A
git commit -m "<approved message>"
```

Do NOT use `--no-verify`.

### 6. Push
```bash
git push origin main
```

### 7. Confirm
Run `git log --oneline -5` and show the user the latest commits confirming the push succeeded.

## Notes
- Never force-push (`--force`) without explicit user instruction
- If the push is rejected (non-fast-forward), report it and ask the user how to proceed — do not auto-rebase or auto-merge
- Never commit `.env` files, secrets, or `frontend/dist/`
