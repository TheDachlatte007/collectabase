# Deploy Collectabase

Deploy the latest code using Docker Compose.

## Steps

1. **Check git status** — confirm there are no uncommitted changes that should be included. If there are staged or unstaged changes, ask the user whether to commit them first before deploying.

2. **Show what's being deployed** — run `git log --oneline -5` to show the last 5 commits so the user knows what will be live.

3. **Build and restart** — run the following commands in order from the project root (`B:/Code/collectabase`):

   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Verify** — run `docker compose ps` and `docker compose logs --tail=30 collectabase` to confirm the container is running and healthy.

5. **Report** — summarize the result: container status, port, and any warnings from logs.

## Notes
- The app runs on port **8000**
- Data is persisted in Docker volumes `collectabase_data` and `collectabase_uploads` — these are never touched by a deploy
- If the build fails, show the full error and do not bring down the running container
- If the user passes `--skip-build`, skip step 3a and only run `docker compose up -d`
