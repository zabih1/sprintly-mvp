# Comprehensive Logging Implementation

## Overview
The Sprintly MVP application now includes comprehensive structured logging throughout all components, providing detailed visibility into:
- File ingestion and CSV processing
- LLM enrichment (OpenAI API calls)
- Embedding generation
- Database operations (PostgreSQL & Neo4j)
- Email generation
- Vector search operations
- API endpoints

## Key Features

### 1. **Structured Logging**
- Consistent log format across all modules
- Contextual information (timestamps, module names, function names)
- Color-coded console output for easy reading
- Separate file logs with full detail

### 2. **Log Levels**
- **DEBUG**: Detailed diagnostic information (entity-level operations)
- **INFO**: General informational messages (progress updates, completion)
- **WARNING**: Warning messages (non-critical issues, fallbacks)
- **ERROR**: Error messages with full stack traces
- **CRITICAL**: Critical failures

### 3. **Log Outputs**
- **Console**: Color-coded, readable format for development
- **File**: Detailed logs saved to `logs/sprintly_YYYYMMDD.log`
- Automatic daily log rotation by date

## Architecture

### Logging Configuration
**File**: `backend/app/core/logging_config.py`

Key components:
```python
# Initialize logging
setup_logging(log_level="INFO", enable_file_logging=True)

# Get logger for a module
logger = get_logger(__name__)

# Log operations with timing
with OperationTimer(logger, "CSV parsing"):
    process_csv()

# Log API calls
log_api_call(logger, "OpenAI", "embeddings.create", 
            model="text-embedding-3-large", count=100, status="success")

# Log progress
log_processing_progress(logger, current=500, total=1000, 
                       operation="Entity enrichment")

# Log errors with context
log_error_with_context(logger, error, "Database operation", 
                       entity_id=123, operation="insert")
```

### Modules with Logging

#### 1. **Main Application** (`app/main.py`)
Logs:
- Application startup/shutdown
- Database initialization
- File upload requests
- Upload completion statistics
- API endpoint errors

Example logs:
```
INFO | 2025-11-14 10:30:15 | app.main | FastAPI application initialized
INFO | 2025-11-14 10:30:15 | app.main | ✓ Database initialized successfully
INFO | 2025-11-14 10:35:20 | app.main | Starting CSV upload: connections.csv | skip_enrichment=False | max_workers=10
INFO | 2025-11-14 10:35:21 | app.main | File loaded: connections.csv | Size: 15.32MB
INFO | 2025-11-14 10:45:30 | app.main | Upload complete: connections.csv | Created: 2500 | Skipped: 100 | Total: 2600
```

#### 2. **Batch Processor** (`app/services/batch_processor.py`)
Logs:
- CSV parsing progress
- Entity extraction (existing vs new)
- Parallel enrichment progress
- Batch embedding generation
- Database commits
- Neo4j graph creation
- Processing statistics and rates

Example logs:
```
INFO | 2025-11-14 10:35:22 | app.services.batch_processor | FAST CSV PROCESSING START
INFO | 2025-11-14 10:35:23 | app.services.batch_processor | CSV parsed successfully | Total connections: 2600
INFO | 2025-11-14 10:35:25 | app.services.batch_processor | Entity extraction complete | Existing: 100 | New: 2500
INFO | 2025-11-14 10:35:25 | app.services.batch_processor | Starting parallel enrichment | Entities: 2500 | Workers: 10
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Progress: Entity enrichment | 2500/2500 (100.0%)
INFO | 2025-11-14 10:40:35 | app.services.batch_processor | Starting batch embedding generation | Total texts: 2500 | Batch size: 2000
INFO | 2025-11-14 10:41:05 | app.services.batch_processor | Completed embedding generation | Total: 2500 | Successful: 2500
INFO | 2025-11-14 10:45:20 | app.services.batch_processor | Step 5: Creating Neo4j graph | Nodes: 2500 | Relationships: 2500
INFO | 2025-11-14 10:45:30 | app.services.batch_processor | PROCESSING COMPLETE
INFO | 2025-11-14 10:45:30 | app.services.batch_processor | Processing time: 615.2 seconds
INFO | 2025-11-14 10:45:30 | app.services.batch_processor | Processing rate: 4.1 entities/second
```

#### 3. **Enrichment Service** (`app/services/enrichment.py`)
Logs:
- LLM API calls for entity enrichment
- Embedding generation
- API failures and retries
- Entity classification results

Example logs:
```
DEBUG | 2025-11-14 10:36:10 | app.services.enrichment | Enriching entity | Name: John Smith | Company: Acme Ventures | Position: Partner
INFO | 2025-11-14 10:36:12 | app.services.enrichment | API Call: OpenAI.chat.completions.create | model=gpt-4o-mini | entity=John Smith | status=success
DEBUG | 2025-11-14 10:36:12 | app.services.enrichment | Entity enriched | Name: John Smith | Role: investor
INFO | 2025-11-14 10:40:35 | app.services.enrichment | API Call: OpenAI.embeddings.create | model=text-embedding-3-large | count=2000 | status=success
```

#### 4. **Neo4j Client** (`app/services/neo4j_client.py`)
Logs:
- Connection establishment
- Node creation
- Relationship creation
- Query execution
- Connection errors

Example logs:
```
INFO | 2025-11-14 10:30:15 | app.services.neo4j_client | Connecting to Neo4j | URI: neo4j://localhost:7687
INFO | 2025-11-14 10:30:16 | app.services.neo4j_client | ✓ Neo4j connection established
DEBUG | 2025-11-14 10:45:20 | app.services.neo4j_client | Created/updated Neo4j node | ID: 123 | Name: John Smith
DEBUG | 2025-11-14 10:45:20 | app.services.neo4j_client | Created Neo4j relationship | 1 -> 123 | Type: CONNECTED_TO
```

#### 5. **Email Generator** (`app/services/email_generator.py`)
Logs:
- Email generation requests
- LLM API calls
- Email generation success/failure
- Multiple tone generation

Example logs:
```
INFO | 2025-11-14 11:00:00 | app.services.email_generator | Generating multiple emails | Tones: formal, casual, enthusiastic | Founder: Jane Doe | Investor: John Smith
INFO | 2025-11-14 11:00:02 | app.services.email_generator | Generating email | Tone: formal | Founder: Jane Doe | Investor: John Smith
INFO | 2025-11-14 11:00:03 | app.services.email_generator | API Call: OpenAI.chat.completions.create | model=gpt-4o-mini | tone=formal | status=success
DEBUG | 2025-11-14 11:00:03 | app.services.email_generator | Email generated successfully | Tone: formal | Length: 450
INFO | 2025-11-14 11:00:10 | app.services.email_generator | Generated 3 email variants
```

#### 6. **Vector Search** (`app/services/vector_search.py`)
Logs:
- Search queries
- Vector embedding generation
- Result counts
- Hybrid search operations

Example logs:
```
INFO | 2025-11-14 11:15:00 | app.services.vector_search | Hybrid search | Query: 'fintech seed MENA' | Filters: role=investor, sector=None, stage=None, location=None
INFO | 2025-11-14 11:15:00 | app.services.vector_search | Vector search | Query: 'fintech seed MENA' | Role: investor | Limit: 20
INFO | 2025-11-14 11:15:01 | app.services.vector_search | Vector search complete | Query: 'fintech seed MENA' | Results: 18
DEBUG | 2025-11-14 11:15:01 | app.services.vector_search | Vector search returned 18 candidates
INFO | 2025-11-14 11:15:01 | app.services.vector_search | Hybrid search complete | Query: 'fintech seed MENA' | Final results: 10
```

## Configuration

### Environment Variables
You can configure logging via environment variables in `.env`:

```bash
# Logging configuration (optional)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENABLE_FILE_LOGGING=true
LOG_FILE_PATH=logs/sprintly.log  # Optional custom path
```

### Programmatic Configuration
In `backend/app/main.py`:

```python
from app.core.logging_config import setup_logging

# Initialize logging
setup_logging(
    log_level="INFO",           # Set log level
    enable_file_logging=True,   # Enable file output
    log_file="custom.log"       # Optional custom file path
)
```

## Log File Management

### Location
Logs are stored in `backend/logs/` directory:
```
backend/
└── logs/
    ├── sprintly_20251114.log
    ├── sprintly_20251113.log
    └── sprintly_20251112.log
```

### Rotation
- Automatic daily rotation (new file each day)
- File naming format: `sprintly_YYYYMMDD.log`
- Manual cleanup: delete old log files as needed

### Size Management
For large deployments, consider:
1. Log rotation tools (logrotate on Linux)
2. Compression of old logs
3. Automated cleanup scripts

Example logrotate configuration:
```
/path/to/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 user group
}
```

## Performance Monitoring

### Key Metrics Logged

#### 1. **Processing Rate**
```
INFO | Processing rate: 4.1 entities/second
```

#### 2. **Operation Timing**
```
INFO | Completed: CSV parsing | Duration: 2.35s
INFO | Completed: Entity enrichment | Duration: 315.2s
INFO | Completed: Batch embedding generation | Duration: 45.8s
```

#### 3. **Progress Tracking**
```
INFO | Progress: Entity enrichment | 500/2500 (20.0%)
INFO | Progress: Embedding generation | 1000/2500 (40.0%) | batch=1-2000
INFO | Progress: Database commit | 2500/2500 (100.0%)
```

#### 4. **API Call Tracking**
```
INFO | API Call: OpenAI.chat.completions.create | model=gpt-4o-mini | entity=John Smith | status=success
INFO | API Call: OpenAI.embeddings.create | model=text-embedding-3-large | count=2000 | status=success
```

## Error Handling

### Error Logging Format
All errors include:
- Full stack trace
- Error type
- Contextual information
- Operation that failed

Example:
```
ERROR | 2025-11-14 10:40:00 | app.services.batch_processor | Error: Batch embedding generation | Type: APIError | Message: Rate limit exceeded | batch=2001-4000
ERROR | 2025-11-14 10:40:00 | app.services.enrichment | Error: Enrich entity | Type: JSONDecodeError | Message: Expecting value: line 1 column 1 (char 0) | name=John Smith | company=Acme Ventures | position=Partner
```

### Error Context
Errors include relevant context for debugging:
- Entity IDs
- File names
- API parameters
- Database operations
- Network requests

## Debugging Tips

### 1. **Enable Debug Logging**
For detailed diagnostics:
```python
setup_logging(log_level="DEBUG")
```

### 2. **Search Logs**
Common searches:
```bash
# Find all errors
grep "ERROR" logs/sprintly_20251114.log

# Find specific entity processing
grep "entity_id=123" logs/sprintly_20251114.log

# Find API calls
grep "API Call: OpenAI" logs/sprintly_20251114.log

# Find slow operations
grep "Duration:" logs/sprintly_20251114.log | grep -v "0\.[0-9]s"
```

### 3. **Monitor Real-time**
```bash
# Tail logs in real-time
tail -f logs/sprintly_20251114.log

# Filter for specific level
tail -f logs/sprintly_20251114.log | grep "INFO"

# Watch errors only
tail -f logs/sprintly_20251114.log | grep "ERROR\|CRITICAL"
```

## Best Practices

### 1. **Log Levels**
- **DEBUG**: Use for detailed diagnostic information (disabled in production)
- **INFO**: Use for important business events and progress
- **WARNING**: Use for recoverable issues (API retry, fallback used)
- **ERROR**: Use for failures that need investigation
- **CRITICAL**: Use for system-level failures

### 2. **Sensitive Data**
The logging system automatically avoids logging:
- API keys
- Passwords
- Email content (only metadata logged)
- Personal identifiable information (PII)

### 3. **Performance**
- File logging is asynchronous (no blocking)
- Console output uses buffering
- Debug logs only evaluated when debug level is active

### 4. **Production Recommendations**
For production deployment:
1. Set log level to INFO (not DEBUG)
2. Enable file logging
3. Set up log rotation
4. Monitor log file sizes
5. Configure centralized logging (e.g., ELK stack, CloudWatch)

## Integration with Monitoring Tools

### 1. **ELK Stack (Elasticsearch, Logstash, Kibana)**
Configure Logstash to read log files:
```conf
input {
  file {
    path => "/path/to/backend/logs/*.log"
    type => "sprintly"
  }
}

filter {
  grok {
    match => { "message" => "%{LOGLEVEL:level} \| %{TIMESTAMP_ISO8601:timestamp} \| %{DATA:module} \| %{GREEDYDATA:message}" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "sprintly-%{+YYYY.MM.dd}"
  }
}
```

### 2. **AWS CloudWatch**
Use AWS CloudWatch agent or boto3:
```python
import boto3
import watchtower

logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='sprintly-mvp',
    stream_name='application'
))
```

### 3. **Datadog**
```python
from datadog import initialize, statsd

initialize(api_key='YOUR_KEY', app_key='YOUR_APP_KEY')
# Logs automatically forwarded via Datadog agent
```

## Troubleshooting

### Issue: Logs not appearing
**Solution**: Check log level configuration
```python
# Ensure logging is initialized
setup_logging(log_level="DEBUG")  # Increase verbosity
```

### Issue: Log files too large
**Solution**: 
1. Reduce log level (INFO instead of DEBUG)
2. Set up log rotation
3. Clean up old logs regularly

### Issue: Performance impact
**Solution**:
1. Reduce console logging in production
2. Use file logging only
3. Set appropriate log levels

## Examples

### Complete Upload Flow Logs
```
INFO | 2025-11-14 10:30:00 | app.main | Starting CSV upload: connections.csv | skip_enrichment=False | max_workers=10
INFO | 2025-11-14 10:30:01 | app.main | File loaded: connections.csv | Size: 15.32MB
INFO | 2025-11-14 10:30:01 | app.services.batch_processor | FAST CSV PROCESSING START
INFO | 2025-11-14 10:30:02 | app.services.batch_processor | Starting: CSV parsing
INFO | 2025-11-14 10:30:03 | app.services.batch_processor | Completed: CSV parsing | Duration: 1.2s
INFO | 2025-11-14 10:30:03 | app.services.batch_processor | CSV parsed successfully | Total connections: 2600
INFO | 2025-11-14 10:30:05 | app.services.batch_processor | Entity extraction complete | Existing: 100 | New: 2500
INFO | 2025-11-14 10:30:05 | app.services.batch_processor | Starting parallel enrichment | Entities: 2500 | Workers: 10
INFO | 2025-11-14 10:32:00 | app.services.batch_processor | Progress: Entity enrichment | 1000/2500 (40.0%)
INFO | 2025-11-14 10:35:30 | app.services.batch_processor | Completed parallel enrichment | Total: 2500 | Success: 2450
INFO | 2025-11-14 10:35:35 | app.services.batch_processor | Starting batch embedding generation | Total texts: 2500 | Batch size: 2000
INFO | 2025-11-14 10:36:05 | app.services.batch_processor | Completed embedding generation | Total: 2500 | Successful: 2500
INFO | 2025-11-14 10:36:10 | app.services.batch_processor | Creating entities and connections in database...
INFO | 2025-11-14 10:40:00 | app.services.batch_processor | Final commit complete | Total entities created: 2500
INFO | 2025-11-14 10:40:05 | app.services.batch_processor | Step 5: Creating Neo4j graph | Nodes: 2500 | Relationships: 2500
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | ✓ Neo4j graph created | Nodes: 2500 | Relationships: 2500
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | PROCESSING COMPLETE
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Total connections: 2600
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Created: 2500
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Skipped: 100
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Processing time: 630.5 seconds
INFO | 2025-11-14 10:40:30 | app.services.batch_processor | Processing rate: 4.0 entities/second
INFO | 2025-11-14 10:40:30 | app.main | Upload complete: connections.csv | Created: 2500 | Skipped: 100 | Total: 2600
```

---

**Last Updated**: November 14, 2025  
**Version**: 1.0.0  
**Status**: ✅ Fully Implemented

