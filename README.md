# HashWatch

HashWatch is a Python File Integrity Monitoring and Malware Detection tool that detects unauthorized file changes using SHA-256 baselines and real-time filesystem monitoring.

## Current Project Status

HashWatch is fully implemented and working.

- Core commands implemented: create-baseline, update-baseline, check, monitor, add-path, remove-path, list, show-log
- Real-time monitoring implemented via watchdog
- Baseline persistence implemented via JSON
- Security alert logging implemented (console + file)
- Automated tests implemented with pytest
- Latest test status: 10 passed
- Enhancement implemented: monitor mode now persists add/delete/move changes back to the baseline file on disk

## Features

- SHA-256 hashing for files and directories
- Baseline snapshot creation and update
- Integrity diff against baseline: modified, added, deleted
- Real-time monitoring with immediate alerts
- Timestamped event logging to hashwatch.log
- CLI-first workflow for operational usage
- Graceful handling of missing files, permission issues, and malformed baseline JSON

## Repository Layout

```text
HashWatch/
├── .venv/
├── LICENSE
├── README.md                <- this file
└── hashwatch/
    ├── main.py
    ├── hasher.py
    ├── baseline.py
    ├── monitor.py
    ├── alerts.py
    ├── config.py
    ├── requirements.txt
    ├── .gitignore
    ├── hashwatch_baseline.json   (generated at runtime)
    ├── hashwatch.log             (generated at runtime)
    ├── demo/
    └── tests/
        ├── conftest.py
        ├── test_hasher.py
        ├── test_baseline.py
        └── test_alerts.py
```

## How HashWatch Works

HashWatch computes a SHA-256 hash for every monitored file. That hash is a cryptographic fingerprint.

- If file content is unchanged, hash is unchanged.
- If even one byte changes, the hash changes.

Operational flow:

1. Create a trusted baseline from one or more paths.
2. Save baseline to hashwatch_baseline.json.
3. Run check to compare current hashes to baseline.
4. Run monitor for real-time detection of file events.
5. Log all events with timestamps to hashwatch.log.

## Environment Setup

From repository root (HashWatch):

### Windows CMD

```cmd
py -m venv .venv
.venv\Scripts\activate
cd hashwatch
pip install -r requirements.txt
```

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd hashwatch
pip install -r requirements.txt
```

## Command Reference

Run all commands from inside hashwatch folder.

### Create baseline

```bash
python main.py create-baseline --path ./demo
```

What it does:

- Hashes all files under the provided path(s)
- Stores entries and metadata in hashwatch_baseline.json

### Update baseline

```bash
python main.py update-baseline --path ./demo
```

What it does:

- Rebuilds and overwrites the existing baseline

### Check integrity once

```bash
python main.py check --path ./demo
```

What it does:

- Loads baseline
- Re-hashes current files
- Reports modified/added/deleted
- Exit code 0 if clean, 1 if violations found

### Monitor in real time

```bash
python main.py monitor --path ./demo
```

What it does:

- Watches filesystem events continuously
- Emits alerts for modified/added/deleted/moved files
- Press Ctrl+C to stop

Important runtime behavior:

- Added, deleted, and moved-file changes detected during monitor mode are now persisted back into hashwatch_baseline.json automatically.

### Add monitored path

```bash
python main.py add-path --path ./demo/new_scope
```

What it does:

- Loads existing monitored paths
- Adds new path
- Rebuilds baseline with combined scope

### Remove monitored path

```bash
python main.py remove-path --path ./demo/new_scope
```

What it does:

- Removes matching baseline entries under the path prefix
- Updates metadata total_files and paths_monitored

### List baseline metadata

```bash
python main.py list
```

What it prints:

- Baseline creation time
- Total files tracked
- Monitored path list

### Show recent logs

```bash
python main.py show-log --lines 50
```

What it prints:

- Last N lines from hashwatch.log (default 50)

## Example End-to-End Validation

```cmd
cd hashwatch
mkdir demo
echo hello>demo\sample.txt
python main.py create-baseline --path .\demo
python main.py check --path .\demo
```

Then simulate tampering:

```cmd
echo changed>demo\sample.txt
python main.py check --path .\demo
```

Expected result:

- MODIFIED alert appears
- Scan summary shows Modified > 0
- Command exits with code 1

## Logging and Alerts

- Logger name: hashwatch
- Format: %(asctime)s [%(levelname)s] %(message)s
- Date format: %Y-%m-%d %H:%M:%S
- Outputs:
  - File handler to hashwatch.log (append, UTF-8)
  - Stream handler to stdout

## Testing

From hashwatch folder:

```bash
pytest
```

Implemented tests cover:

- Known hash correctness
- Directory hash mapping
- Missing file behavior
- Baseline create/load
- Diff detection for modified/added/deleted files
- Alert logging invocations

## Security Notes

- Uses SHA-256 for integrity fingerprinting.
- Skips symlinks when hashing directories.
- Handles PermissionError and FileNotFoundError during hashing.
- Handles JSONDecodeError and I/O errors during baseline load/save.

## License

MIT
