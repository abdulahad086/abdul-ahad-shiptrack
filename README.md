# ShipTrack: Deployment Tracker API

An internal API that records every software deployment: which application, which version, which environment, and whether it succeeded. Written in FastAPI, backed by PostgreSQL 16.

## Running the API

To spin up the database and the API locally:
```bash
cp .env.example .env
docker compose up --build -d
```

Access Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

## Running Tests & Coverage

To run the full test suite with coverage inside the container:
```bash
docker compose exec -T api pytest --cov=app --cov-report=term-missing --cov-fail-under=60
```

## Nightly Backups (Cron)

To schedule nightly database backups at 02:00 daily, add the following line to your crontab (`crontab -e`):

```cron
0 2 * * * cd /Users/mac/Desktop/abdul-ahad-shiptrack && ./scripts/backup_db.sh >> logs/backup.log 2>&1
```

### Explanation of the Crontab line:
- `0`: Minute (0th minute)
- `2`: Hour (2:00 AM)
- `*`: Day of the Month (every day of the month)
- `*`: Month (every month)
- `*`: Day of the Week (every day of the week)
- `cd /Users/mac/Desktop/abdul-ahad-shiptrack`: Changes the working directory to the absolute path of the repository root. This is critical because cron jobs run with a very minimal default shell environment and in the user's home directory. Changing directory ensures that paths to scripts and outputs are correctly resolved.
- `./scripts/backup_db.sh`: Executes the backup script from the repository root.
- `>> logs/backup.log 2>&1`: Redirects stdout (`>>`) and stderr (`2>&1`) to append to `logs/backup.log`.

## Verifying Live Reload

For local development, the `docker-compose.yml` configures a bind mount mapping the `./app` directory to the container. When code is edited, FastAPI's reloader (via watchfiles) automatically detects the changes and reloads.

1. **File edited**: `app/main.py`
2. **Change made**: Changed the startup log line or a custom test response.
3. **Reloader log**:
   ```
   INFO:     WatchFiles detected changes in 'app/main.py'. Reloading...
   INFO:     Finished reloading
   ```
4. **New response**: Received the updated response immediately without running `docker compose build`.

## Docker Hub Repository

The built Docker image is pushed to:
[https://hub.docker.com/r/abdulahadmujahid/shiptrack](https://hub.docker.com/r/abdulahadmujahid/shiptrack)

### Final Image Size
The final built Docker image size is under 200 MB (well below the 300 MB target limit).
