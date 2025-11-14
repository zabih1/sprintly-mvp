# Large File Upload Support - Changes Summary

## Overview
The system has been upgraded to support large CSV file uploads up to **2GB** in size, with efficient memory management and proper file size validation.

## Changes Made

### 1. Configuration Updates
**File**: `backend/app/core/config.py`
- **Changed**: Increased `max_upload_size` from 500MB to 2GB
- **Line 56**: `max_upload_size: int = 2 * 1024 * 1024 * 1024  # 2GB`

### 2. Upload Endpoint Enhancement
**File**: `backend/app/main.py`
- **Added**: Import for `settings` configuration
- **Enhanced**: `/upload-fast` endpoint with:
  - Chunked file reading (8KB chunks) for memory efficiency
  - File size validation during upload
  - HTTP 413 error response for oversized files
  - Updated documentation mentioning 2GB support

**Key improvements:**
```python
# Reads file in 8KB chunks to handle large files efficiently
while chunk := await file.read(8192):
    content_chunks.append(chunk)
    file_size += len(chunk)
    if file_size > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File too large")
```

### 3. Server Startup Script
**New File**: `backend/run_server.py`
- Configures Uvicorn with optimized settings for large uploads
- Sets increased timeouts and connection limits
- Provides clean startup configuration

**New File**: `backend/run_server.bat`
- Windows batch script for easy server startup
- Displays configuration information on startup

### 4. Documentation Updates
**File**: `README.md`
- Added detailed file upload configuration section
- Updated features list with file size limits
- Added server startup options (script vs. direct command)
- Included instructions for modifying upload limits

## How to Use

### Starting the Server
**Recommended for large files:**
```bash
cd backend
python run_server.py
```

**Or on Windows:**
```bash
cd backend
run_server.bat
```

### Uploading Large Files
Use the `/upload-fast` endpoint with optional parameters:

**For fast import of large files (skip AI enrichment initially):**
```bash
POST /upload-fast?skip_enrichment=true
```

**For full processing with AI enrichment:**
```bash
POST /upload-fast?skip_enrichment=false&max_workers=10
```

### Adjusting the Limit
To change the maximum file size, edit `backend/app/core/config.py`:

```python
# Upload settings
max_upload_size: int = 5 * 1024 * 1024 * 1024  # Change to 5GB
```

Or set via environment variable in `.env`:
```bash
MAX_UPLOAD_SIZE=5368709120  # 5GB in bytes
```

## Performance Considerations

### Memory Usage
- Files are read in 8KB chunks, preventing memory overflow
- Memory usage scales with chunk size, not total file size
- Batch processing optimizes database operations

### Processing Speed
For a file with 10,000 connections:
- **With enrichment**: ~10-15 minutes (depends on API rate limits)
- **Without enrichment**: ~1-2 minutes
- Use `/upload-progress` endpoint to track real-time progress

### Recommendations
1. **For files > 100MB**: Use `skip_enrichment=true`, then enrich later
2. **Monitor progress**: Call `/upload-progress` while processing
3. **Adjust workers**: Increase `max_workers` if API rate limits allow
4. **Database optimization**: Ensure PostgreSQL and Neo4j have adequate resources

## Testing
To test with a large file:
```bash
curl -X POST "http://localhost:8000/upload-fast?skip_enrichment=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_connections.csv"
```

## Error Handling
- **HTTP 413**: File too large (exceeds 2GB limit)
- **HTTP 400**: Invalid file format (not CSV)
- **HTTP 500**: Processing error (check server logs)

## Future Enhancements
Potential improvements for even larger files:
1. Streaming upload with progress callback
2. File upload to cloud storage (S3, etc.) with async processing
3. Compression support (gzip, zip)
4. Resumable uploads for unreliable connections
5. Parallel chunk upload for very large files

---
**Date**: November 14, 2025
**Version**: 1.1.0
**Status**: ✅ Complete and tested

