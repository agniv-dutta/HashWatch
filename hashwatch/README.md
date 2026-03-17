# HashWatch

File Integrity Monitoring and Malware Detection Tool for proactive tamper detection.

## Features

- Generates SHA-256 hashes for files and directories.
- Creates a persistent baseline in JSON for trusted file states.
- Detects modified, added, and deleted files with clear alerts.
- Monitors files in real time using watchdog.
- Logs all security events with timestamps to `hashwatch.log`.
- Provides a complete command-line interface for operations and reporting.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run commands from the project root (`hashwatch/`):

### 1. Create Baseline

```bash
python main.py create-baseline --path ./project
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Hashing: project/main.py
Hashing: project/utils.py
Hashing: project/config.json
Baseline created: 3 files indexed.
```

### 2. Update Baseline

```bash
python main.py update-baseline --path ./project
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Hashing: project/main.py
Hashing: project/utils.py
Baseline created: 2 files indexed.
Baseline updated.
```

### 3. Check Integrity

```bash
python main.py check --path ./project
```

Sample output (violations):

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Hashing: project/main.py
Hashing: project/utils.py
Hashing: project/config.json
2026-03-17 14:02:00 [WARNING] [ALERT] MODIFIED: project/config.json
  Expected : 3a7bd3e2360a3d29...
  Found    : 9f86d081884c7d65...

SCAN COMPLETE
─────────────────
Modified : 1
Added    : 0
Deleted  : 0
─────────────────
```

Exit code behavior:

- `0` when no integrity violations are found.
- `1` when modified, added, or deleted files are detected.

### 4. Monitor in Real Time

```bash
python main.py monitor --path ./project
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
HashWatch is monitoring. Press Ctrl+C to stop.
2026-03-17 14:05:11 [WARNING] [ALERT] MODIFIED: project/config.json
  Expected : 3a7bd3e2...
  Found    : 9f86d081...
```

Stop monitoring with `Ctrl+C`.

### 5. Add a New Path to Baseline

```bash
python main.py add-path --path ./project/new_module
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Hashing: project/main.py
Hashing: project/new_module/service.py
Baseline created: 2 files indexed.
Path added to baseline: project/new_module
```

### 6. Remove a Path from Baseline

```bash
python main.py remove-path --path ./project/new_module
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Removed 4 entries for path: project/new_module
```

### 7. List Baseline Metadata

```bash
python main.py list
```

Sample output:

```text
╔══════════════════════════════╗
║   HashWatch v1.0.0           ║
║   File Integrity Monitor     ║
╚══════════════════════════════╝
Baseline Metadata
─────────────────
Created at : 2026-03-17T14:00:00+00:00
Total files: 15
Monitored paths:
  - project
  - project/config
```

### 8. Show Security Log Tail

```bash
python main.py show-log --lines 100
```

Sample output:

```text
2026-03-17 14:00:00 [INFO] Scan started for: ['project']
2026-03-17 14:02:00 [WARNING] [ALERT] MODIFIED: project/config.json
2026-03-17 14:02:00 [WARNING] [ALERT] NEW FILE DETECTED: project/suspicious.bin
```

## How It Works

HashWatch uses SHA-256, a cryptographic hashing algorithm, to create a unique fingerprint for each file. If even one byte changes, the SHA-256 output changes significantly. HashWatch stores trusted fingerprints in a baseline file and compares fresh scans against that baseline.

- Same hash as baseline: file is unchanged.
- Different hash: file was modified.
- New file not in baseline: file was added.
- Baseline file missing from current scan: file was deleted.

This approach is effective for detecting unauthorized changes that may indicate malware activity, tampering, or operational drift.

## Project Structure

```text
hashwatch/
├── main.py
├── hasher.py
├── baseline.py
├── monitor.py
├── alerts.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    ├── test_hasher.py
    ├── test_baseline.py
    └── test_alerts.py
```

## License

MIT
