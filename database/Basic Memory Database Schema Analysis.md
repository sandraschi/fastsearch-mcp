---
title: Basic Memory Database Schema Analysis
type: note
permalink: database-basic-memory-database-schema-analysis
---

# Basic Memory SQLite Database Schema Analysis

**Database Location**: `C:\Users\sandr\.basic-memory\memory.db`  
**Analysis Date**: July 15, 2025  
**Purpose**: Understanding schema for data extraction from memory_borked.db  

## Database Files

### Main Files

- `memory.db` - Primary database
- `memory_borked.db` - Corrupted/problematic database we need to extract from
- `memory - Copy.db` & `memory - Copy (2).db` - Backup copies

### Related Files

- `bm_db_fix.sql` - Repair scripts
- `cleanup.sql`, `conservative_cleanup.sql` - Data cleanup scripts
- `investigate_myai.sql`, `investigate_veogen.sql` - Project analysis scripts
- `preview.sql`, `preview_cleanup.sql` - Preview scripts for operations

## Database Schema (Inferred from SQL Files)

### Core Tables

#### 1. `project` Table

```sql
-- Primary projects table
CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL
);
```

**Purpose**: Manages different Basic Memory projects  
**Current Projects** (from config.json):

- `main` → `C:\Users\sandr\basic-memory`
- `plexmcp` → `C:\Users\sandr\AppData\Local\AnthropicClaude\app-0.11.6\PlexMCP`
- `myai` → `d:\dev\repos\myai`
- `claude-depot-consolidated` → `C:\Users\sandr\Documents\claude-depot`
- `veogen` → `D:\dev\repos\veogen`
- `general-ai` → `C:\Users\sandr\Documents\general-ai`

#### 2. `entity` Table

```sql
-- Main entities table - files, notes, concepts
CREATE TABLE entity (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    file_path TEXT,
    entity_type TEXT,
    title TEXT,
    content TEXT,
    checksum TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    -- Additional metadata fields
);
```

**Purpose**: Stores all content entities (files, notes, markdown documents)  
**Key Fields**:

- `file_path` - Full filesystem path to the file
- `entity_type` - Type of entity (note, file, etc.)
- `title` - Display title
- `content` - Full text content for indexing
- `checksum` - For change detection

#### 3. `observation` Table

```sql
-- Observations/relations between entities
CREATE TABLE observation (
    id INTEGER PRIMARY KEY,
    entity_id INTEGER REFERENCES entity(id),
    observation_type TEXT,
    content TEXT,
    metadata JSON,
    created_at TIMESTAMP
);
```

**Purpose**: Stores relationships, observations, and connections between entities

### Index Structure

The database likely includes indexes on:

- `entity.file_path` - For fast file lookups
- `entity.project_id` - For project filtering
- `entity.entity_type` - For type filtering
- `observation.entity_id` - For relationship queries

## Common Query Patterns

### File Type Analysis

```sql
-- Categorize files by type/location
SELECT 
    CASE 
        WHEN file_path LIKE '%/build/%' OR file_path LIKE '%\\build\\%' THEN 'BUILD_DIRS'
        WHEN file_path LIKE '%/dist/%' OR file_path LIKE '%\\dist\\%' THEN 'DIST_DIRS'
        WHEN file_path LIKE '%node_modules%' THEN 'NODE_MODULES'
        WHEN file_path LIKE '%/.cache/%' OR file_path LIKE '%\\.cache\\%' THEN 'CACHE_DIRS'
        WHEN file_path LIKE '%/venv/%' OR file_path LIKE '%\\venv\\%' THEN 'PYTHON_VENV'
        WHEN file_path LIKE '%/__pycache__/%' OR file_path LIKE '%\\__pycache__\\%' THEN 'PYTHON_CACHE'
        ELSE 'OTHER'
    END as file_type,
    COUNT(*) as count
FROM entity e
JOIN project p ON e.project_id = p.id
WHERE p.name = 'myai'
GROUP BY file_type
ORDER BY count DESC;
```

### Duplicate Detection

```sql
-- Find duplicate file entries
SELECT file_path, COUNT(*) as count
FROM entity 
GROUP BY file_path, project_id 
HAVING COUNT(*) > 1
ORDER BY count DESC;
```

### Orphaned Records Cleanup

```sql
-- Clean up orphaned observations
DELETE FROM observation 
WHERE entity_id NOT IN (SELECT id FROM entity);
```

## Performance Issues Identified

### 1. Node Modules Explosion

- **Problem**: `node_modules` directories contain 100,000+ files
- **Impact**: Makes database huge and sync extremely slow
- **Solution**: Exclude `node_modules`, `build`, `dist`, cache directories

### 2. Build Artifacts

- **Problem**: Temporary build files being indexed
- **Categories**: `build/`, `dist/`, `.cache/`, `__pycache__/`, `.temp/`
- **Solution**: Implement exclusion patterns

### 3. Virtual Environments

- **Problem**: Python `venv/` and similar environments indexed
- **Impact**: Thousands of unnecessary files tracked
- **Solution**: Add to exclusion list

## Data Extraction Strategy for memory_borked.db

### 1. Schema Verification

```sql
-- Check if schema matches expected structure
.schema
```

### 2. Data Integrity Check

```sql
-- Check for corruption
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

### 3. Safe Data Export

```sql
-- Export projects
SELECT * FROM project;

-- Export entities with filtering
SELECT * FROM entity 
WHERE file_path NOT LIKE '%node_modules%'
  AND file_path NOT LIKE '%/build/%'
  AND file_path NOT LIKE '%\\build\\%'
  AND file_path NOT LIKE '%/.cache/%'
  AND file_path NOT LIKE '%\\.cache\\%';

-- Export observations
SELECT * FROM observation;
```

### 4. Recovery Commands

```bash
# Create clean database from borked one
sqlite3 memory_borked.db ".dump" | sqlite3 memory_recovered.db

# Export specific tables
sqlite3 memory_borked.db ".dump project" > projects.sql
sqlite3 memory_borked.db ".dump entity" > entities.sql
```

## Maintenance Queries

### Database Size Analysis

```sql
-- Check table sizes
SELECT 
    name,
    (SELECT COUNT(*) FROM pragma_table_info(name)) as columns,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=name) as indexes
FROM sqlite_master 
WHERE type='table';
```

### Content Analysis

```sql
-- Analyze content distribution by project
SELECT 
    p.name as project_name,
    COUNT(e.id) as entity_count,
    AVG(LENGTH(e.content)) as avg_content_length,
    SUM(LENGTH(e.content)) as total_content_size
FROM project p
LEFT JOIN entity e ON p.id = e.project_id
GROUP BY p.name
ORDER BY entity_count DESC;
```

---

**Next Steps for Recovery**:

1. Run integrity check on memory_borked.db
2. Export clean data excluding problematic paths
3. Create new database with filtered content
4. Implement exclusion patterns to prevent future issues
