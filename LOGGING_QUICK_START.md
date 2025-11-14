# Logging Quick Start Guide

## 🚀 Getting Started

Logging is automatically enabled when you start the application. No configuration needed!

## 📊 What Gets Logged?

### ✅ All Operations
- **CSV File Uploads** - File size, processing time, results
- **LLM Enrichment** - OpenAI API calls, entity classification
- **Embedding Generation** - Batch processing, success rates
- **Database Operations** - PostgreSQL inserts, Neo4j graph creation
- **Email Generation** - Template rendering, API calls
- **Vector Search** - Query parameters, result counts
- **Errors** - Full stack traces with context

## 📁 Where Are the Logs?

### Console (During Development)
Colored, easy-to-read output in your terminal:
- 🟢 Green = INFO (normal operations)
- 🟡 Yellow = WARNING (non-critical issues)
- 🔴 Red = ERROR (failures)
- 🔵 Cyan = DEBUG (detailed info)

### Log Files (Production)
Location: `backend/logs/sprintly_YYYYMMDD.log`

Examples:
```
backend/logs/
├── sprintly_20251114.log  ← Today's logs
├── sprintly_20251113.log  ← Yesterday
└── sprintly_20251112.log  ← 2 days ago
```

## 🔍 Common Commands

### View Real-Time Logs
```bash
tail -f backend/logs/sprintly_20251114.log
```

### View Only Errors
```bash
grep "ERROR" backend/logs/sprintly_20251114.log
```

### Monitor Upload Progress
```bash
grep "Progress:" backend/logs/sprintly_20251114.log
```

### Check API Calls
```bash
grep "API Call: OpenAI" backend/logs/sprintly_20251114.log
```

### Find Slow Operations (>10 seconds)
```bash
grep "Duration:" backend/logs/sprintly_20251114.log | grep -E "[1-9][0-9]\.[0-9]+s"
```

## 📝 Example Log Output

### Successful Upload
```
INFO | 2025-11-14 10:30:00 | app.main | Starting CSV upload: connections.csv | skip_enrichment=False
INFO | 2025-11-14 10:30:01 | app.main | File loaded: connections.csv | Size: 15.32MB
INFO | 2025-11-14 10:30:02 | app.services.batch_processor | CSV parsed successfully | Total connections: 2600
INFO | 2025-11-14 10:30:05 | app.services.batch_processor | Entity extraction complete | Existing: 100 | New: 2500
INFO | 2025-11-14 10:35:30 | app.services.batch_processor | Completed parallel enrichment | Total: 2500 | Success: 2450
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | PROCESSING COMPLETE
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Processing time: 630.5 seconds
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Processing rate: 4.0 entities/second
INFO | 2025-11-14 10:40:30 | app.main | Upload complete | Created: 2500 | Skipped: 100 | Total: 2600
```

### Error Example
```
ERROR | 2025-11-14 10:35:20 | app.services.enrichment | Error: Enrich entity | Type: APIError | Message: Rate limit exceeded | name=John Smith
ERROR | 2025-11-14 10:35:20 | app.services.enrichment | Traceback (most recent call last):
  File "app/services/enrichment.py", line 68, in enrich_entity
    response = openai.chat.completions.create(...)
  openai.RateLimitError: Rate limit exceeded
```

## ⚙️ Configuration

### Change Log Level
Edit `backend/app/main.py`:
```python
# For more detailed logs
setup_logging(log_level="DEBUG")

# For production (less verbose)
setup_logging(log_level="INFO")

# For critical only
setup_logging(log_level="ERROR")
```

### Disable File Logging (Console Only)
```python
setup_logging(log_level="INFO", enable_file_logging=False)
```

## 🐛 Debugging Tips

### 1. **Upload Not Working?**
```bash
# Check for errors in logs
grep "upload" backend/logs/sprintly_*.log | grep "ERROR"
```

### 2. **Enrichment Failing?**
```bash
# Check OpenAI API calls
grep "API Call: OpenAI" backend/logs/sprintly_*.log
grep "enrichment" backend/logs/sprintly_*.log | grep "ERROR"
```

### 3. **Slow Processing?**
```bash
# Check processing rates and timings
grep "Processing rate" backend/logs/sprintly_*.log
grep "Duration:" backend/logs/sprintly_*.log
```

### 4. **Database Issues?**
```bash
# Check database operations
grep "Database\|PostgreSQL\|Neo4j" backend/logs/sprintly_*.log
```

## 📈 Monitor Performance

### Key Metrics in Logs

1. **Processing Rate**
   ```
   INFO | Processing rate: 4.1 entities/second
   ```

2. **Operation Timing**
   ```
   INFO | Completed: Batch embedding generation | Duration: 45.8s
   ```

3. **Progress Tracking**
   ```
   INFO | Progress: Entity enrichment | 1000/2500 (40.0%)
   ```

4. **API Success Rate**
   ```bash
   # Count successful API calls
   grep "API Call: OpenAI" backend/logs/sprintly_*.log | grep "status=success" | wc -l
   
   # Count failed API calls
   grep "API Call: OpenAI" backend/logs/sprintly_*.log | grep "status=failed" | wc -l
   ```

## 🧹 Log Maintenance

### Clean Up Old Logs (Manual)
```bash
# Delete logs older than 30 days
find backend/logs/ -name "*.log" -mtime +30 -delete
```

### Compress Old Logs
```bash
# Compress logs from previous days
gzip backend/logs/sprintly_2025*.log
```

### Check Log Disk Usage
```bash
# See total log directory size
du -sh backend/logs/

# List log files by size
ls -lh backend/logs/
```

## 🎯 Best Practices

### Development
- ✅ Use console output (automatic)
- ✅ Set log level to DEBUG for detailed info
- ✅ Keep logs directory in .gitignore

### Production
- ✅ Use file logging (automatic)
- ✅ Set log level to INFO (default)
- ✅ Set up log rotation
- ✅ Monitor disk space
- ✅ Set up alerts for ERROR logs

## 🔗 Integration Examples

### Grep for Specific Entity
```bash
# Find all logs for a specific entity ID
grep "entity_id=123" backend/logs/sprintly_*.log

# Find all logs for a specific file
grep "connections.csv" backend/logs/sprintly_*.log
```

### Count Operations
```bash
# Count total uploads today
grep "Upload complete" backend/logs/sprintly_$(date +%Y%m%d).log | wc -l

# Count total entities created today
grep "Total entities created" backend/logs/sprintly_$(date +%Y%m%d).log
```

### Monitor Real-Time with Filters
```bash
# Watch only INFO and ERROR
tail -f backend/logs/sprintly_*.log | grep -E "INFO|ERROR"

# Watch only enrichment operations
tail -f backend/logs/sprintly_*.log | grep "enrichment"

# Watch progress updates
tail -f backend/logs/sprintly_*.log | grep "Progress:"
```

## 💡 Pro Tips

1. **Use Multiple Terminals**
   - Terminal 1: Run the application
   - Terminal 2: `tail -f` logs for monitoring
   - Terminal 3: Grep logs for analysis

2. **Save Important Searches**
   ```bash
   # Create aliases in ~/.bashrc or ~/.zshrc
   alias log-errors='grep "ERROR" backend/logs/sprintly_$(date +%Y%m%d).log'
   alias log-watch='tail -f backend/logs/sprintly_$(date +%Y%m%d).log'
   alias log-api='grep "API Call:" backend/logs/sprintly_$(date +%Y%m%d).log'
   ```

3. **Export Logs for Analysis**
   ```bash
   # Export today's errors to file
   grep "ERROR" backend/logs/sprintly_$(date +%Y%m%d).log > errors_today.txt
   
   # Export API call stats
   grep "API Call:" backend/logs/sprintly_*.log > api_calls.txt
   ```

## 📚 More Information

For detailed documentation, see:
- [LOGGING_IMPLEMENTATION.md](LOGGING_IMPLEMENTATION.md) - Complete technical documentation
- [LOGGING_CHANGES_SUMMARY.md](LOGGING_CHANGES_SUMMARY.md) - What was changed
- [README.md](README.md) - General project documentation

## 🆘 Need Help?

Common issues and solutions:

**Q: No logs appearing in console?**  
A: Check that logging is initialized in `main.py`

**Q: Log files not being created?**  
A: Check `enable_file_logging=True` in setup

**Q: Logs too verbose?**  
A: Change log level from DEBUG to INFO

**Q: Can't find log files?**  
A: Check `backend/logs/` directory (created automatically)

**Q: Want to disable colors?**  
A: Redirect output: `python run_server.py 2>&1 | cat`

---

**Quick Reference Card**
```
📊 View logs:     tail -f backend/logs/sprintly_YYYYMMDD.log
🔍 Find errors:   grep "ERROR" backend/logs/*.log
📈 Check progress: grep "Progress:" backend/logs/*.log
⚡ API calls:     grep "API Call:" backend/logs/*.log
🧹 Clean old:     find backend/logs/ -mtime +30 -delete
```

