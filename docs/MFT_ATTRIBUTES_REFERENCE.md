# NTFS MFT Attributes Reference

## Available Attributes in MFT Records

The NTFS Master File Table (MFT) stores files as collections of attributes. Each attribute contains specific metadata or data.

### Currently Read: $FILE_NAME (0x30) and $STANDARD_INFORMATION (0x10) ✅

**Location**: `service/src/mft_search.cpp` - `FILE_NAME_ATTRIBUTE` structure

**Contains**:
- `ParentDirectory` (ULONGLONG) - MFT record number of parent directory
- `CreationTime` (ULONGLONG) - File creation timestamp (100-nanosecond intervals since 1601-01-01)
- `ModificationTime` (ULONGLONG) - Last modification timestamp
- `MftModificationTime` (ULONGLONG) - MFT record modification timestamp
- `AccessTime` (ULONGLONG) - Last access timestamp
- `AllocatedSize` (ULONGLONG) - Allocated size on disk
- `RealSize` (ULONGLONG) - Actual file size
- `Flags` (DWORD) - File attributes:
  - `0x01` - READONLY
  - `0x02` - HIDDEN
  - `0x04` - SYSTEM
  - `0x10` - DIRECTORY
  - `0x20` - ARCHIVE
  - `0x40` - DEVICE
  - `0x80` - NORMAL
  - `0x100` - TEMPORARY
  - `0x200` - SPARSE_FILE
  - `0x400` - REPARSE_POINT
  - `0x800` - COMPRESSED
  - `0x1000` - OFFLINE
  - `0x2000` - NOT_CONTENT_INDEXED
  - `0x4000` - ENCRYPTED
- `ReparseValue` (DWORD) - Reparse point tag
- `NameLength` (BYTE) - Length of filename
- `NameType` (BYTE) - 0=POSIX, 1=Win32, 2=DOS, 3=Win32+DOS
- `Name` (WCHAR[]) - Filename (Unicode)

### Currently Read: $STANDARD_INFORMATION (0x10) ✅

**Location**: `service/src/mft_search.cpp` - `STANDARD_INFORMATION_ATTRIBUTE` structure

**Contains additional metadata**:

- `CreationTime` (ULONGLONG) - Creation timestamp
- `ModificationTime` (ULONGLONG) - Modification timestamp
- `MftModificationTime` (ULONGLONG) - MFT modification timestamp
- `AccessTime` (ULONGLONG) - Access timestamp
- `FileAttributes` (DWORD) - Same flags as $FILE_NAME
- `MaximumVersions` (DWORD) - Maximum versions
- `VersionNumber` (DWORD) - Version number
- `ClassId` (DWORD) - Class ID
- `OwnerId` (DWORD) - Owner SID (Security Identifier)
- `SecurityId` (DWORD) - Security descriptor ID
- `QuotaCharged` (ULONGLONG) - Quota charged
- `Usn` (ULONGLONG) - Update Sequence Number (USN)

### Other Available Attributes (Not Currently Used)

- **$ATTRIBUTE_LIST (0x20)**: Lists locations of attributes that don't fit in MFT record
- **$OBJECT_ID (0x40)**: Unique GUID for file tracking
- **$SECURITY_DESCRIPTOR (0x50)**: Full security descriptor (ACLs, owner, etc.)
- **$DATA (0x80)**: File content (can have multiple streams)
- **$INDEX_ROOT (0x90)**: Directory index root
- **$INDEX_ALLOCATION (0xA0)**: Directory index allocation
- **$BITMAP (0xB0)**: Allocation bitmap

## Search Capabilities We Should Support

Based on available MFT attributes, we can search/filter by:

### 1. Filename Patterns
- ✅ Currently supported: Glob patterns (*, ?)
- Should add: Regex patterns, exact match, case-sensitive option

### 2. File Size
- ✅ Currently available: `RealSize`, `AllocatedSize` from $FILE_NAME
- Should add: Min/max size filters

### 3. Timestamps
- ✅ Currently available: `ModificationTime` from $FILE_NAME
- Should add: Filters for:
  - Creation time (before/after)
  - Modification time (before/after) - currently only returned, not filterable
  - Access time (before/after)
  - MFT modification time (before/after)

### 4. File Attributes (Flags)
- ✅ Currently available: `Flags` from $FILE_NAME
- ✅ Currently used: Directory detection
- Should add: Filters for:
  - Readonly files
  - Hidden files
  - System files
  - Archive files
  - Compressed files
  - Encrypted files
  - Reparse points (symlinks/junctions)
  - Temporary files
  - Sparse files

### 5. Parent Directory
- ✅ Currently available: `ParentDirectory` from $FILE_NAME
- Should add: Filter by parent directory MFT record number or path

### 6. Owner/Security
- ⚠️ Available in $STANDARD_INFORMATION: `OwnerId`, `SecurityId`
- Should add: Filter by owner SID or security descriptor

### 7. Multiple Filenames
- ⚠️ Files can have multiple $FILE_NAME attributes (long name, short 8.3 name, POSIX name)
- Should add: Search both long and short names

## Implementation Priority

1. **High Priority** (Most useful):
   - Read $STANDARD_INFORMATION for additional timestamps and owner info
   - Add file size filters (min/max)
   - Add timestamp filters (created/modified/accessed before/after)
   - Add file attribute filters (readonly, hidden, system, etc.)
   - Support multiple $FILE_NAME attributes (long + short names)

2. **Medium Priority**:
   - Parent directory filtering
   - Owner/Security filtering
   - Regex pattern support
   - Case-sensitive option

3. **Low Priority** (Advanced):
   - $OBJECT_ID filtering
   - $REPARSE_POINT type filtering
   - Multiple data stream detection

