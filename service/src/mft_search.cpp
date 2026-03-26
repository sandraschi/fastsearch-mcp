// NTFS MFT Search Implementation
// Direct Master File Table access for fast file searching - NO TREE WALKING!

#include "fastsearch_service.h"
#include <winioctl.h>
#include <regex>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <thread>
#include <mutex>
#include <atomic>

namespace {

// Safety limits for unlimited searches
// Maximum safe number of results to prevent memory exhaustion
const int MAX_SAFE_RESULTS = 10000000;  // 10 million files
const int WARN_RESULTS_THRESHOLD = 1000000;  // Warn at 1 million files

// NTFS MFT structures
#pragma pack(push, 1)
struct MFT_RECORD_HEADER {
    DWORD Signature;  // "FILE"
    WORD UpdateSequenceOffset;
    WORD UpdateSequenceSize;
    ULONGLONG LogFileSequenceNumber;
    WORD SequenceNumber;
    WORD LinkCount;
    WORD AttributeOffset;
    ULONGLONG BaseRecordReference;
    WORD NextAttributeId;
    WORD Padding;
    DWORD RecordNumber;
    WORD Flags;
    DWORD RealSize;
    DWORD AllocatedSize;
};

struct ATTRIBUTE_HEADER {
    DWORD Type;
    DWORD Length;
    BYTE NonResident;
    BYTE NameLength;
    WORD NameOffset;
    WORD Flags;
    WORD AttributeId;
};

struct RESIDENT_ATTRIBUTE {
    ATTRIBUTE_HEADER Header;
    DWORD ValueLength;
    WORD ValueOffset;
    BYTE IndexedFlag;
    BYTE Padding;
};

struct FILE_NAME_ATTRIBUTE {
    ULONGLONG ParentDirectory;
    ULONGLONG CreationTime;
    ULONGLONG ModificationTime;
    ULONGLONG MftModificationTime;
    ULONGLONG AccessTime;
    ULONGLONG AllocatedSize;
    ULONGLONG RealSize;
    DWORD Flags;
    DWORD ReparseValue;
    BYTE NameLength;
    BYTE NameType;
    WCHAR Name[1];
};

struct STANDARD_INFORMATION_ATTRIBUTE {
    ULONGLONG CreationTime;
    ULONGLONG ModificationTime;
    ULONGLONG MftModificationTime;
    ULONGLONG AccessTime;
    DWORD FileAttributes;
    DWORD MaximumVersions;
    DWORD VersionNumber;
    DWORD ClassId;
    DWORD OwnerId;
    DWORD SecurityId;
    ULONGLONG QuotaCharged;
    ULONGLONG Usn;
};
#pragma pack(pop)

// Constants (use existing Windows definitions where possible)
static const DWORD MFT_ATTR_STANDARD_INFORMATION = 0x10;
static const DWORD MFT_ATTR_FILE_NAME = 0x30;
static const DWORD MFT_ATTR_END = 0xFFFFFFFF;
static const DWORD MFT_SIGNATURE = 0x454C4946;  // "FILE"

// File attribute flags (use Windows definitions, but define if not available)
#ifndef FILE_ATTRIBUTE_READONLY
#define FILE_ATTRIBUTE_READONLY 0x01
#endif
#ifndef FILE_ATTRIBUTE_HIDDEN
#define FILE_ATTRIBUTE_HIDDEN 0x02
#endif
#ifndef FILE_ATTRIBUTE_SYSTEM
#define FILE_ATTRIBUTE_SYSTEM 0x04
#endif
#ifndef FILE_ATTRIBUTE_DIRECTORY
#define FILE_ATTRIBUTE_DIRECTORY 0x10
#endif
#ifndef FILE_ATTRIBUTE_ARCHIVE
#define FILE_ATTRIBUTE_ARCHIVE 0x20
#endif
#ifndef FILE_ATTRIBUTE_COMPRESSED
#define FILE_ATTRIBUTE_COMPRESSED 0x800
#endif
#ifndef FILE_ATTRIBUTE_ENCRYPTED
#define FILE_ATTRIBUTE_ENCRYPTED 0x4000
#endif

// Helper: Extract string from JSON
std::string ExtractJsonString(const std::string& json, const std::string& key) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return "";
    
    pos = json.find(':', pos);
    if (pos == std::string::npos) return "";
    
    pos = json.find('"', pos);
    if (pos == std::string::npos) return "";
    pos++;
    
    size_t endPos = json.find('"', pos);
    if (endPos == std::string::npos) return "";
    
    return json.substr(pos, endPos - pos);
}

// Helper: Extract integer from JSON
int ExtractJsonInt(const std::string& json, const std::string& key, int defaultValue = 0) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return defaultValue;
    
    pos = json.find(':', pos);
    if (pos == std::string::npos) return defaultValue;
    
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    
    size_t endPos = pos;
    while (endPos < json.length() && 
           json[endPos] >= '0' && json[endPos] <= '9') endPos++;
    
    if (endPos > pos) {
        return std::stoi(json.substr(pos, endPos - pos));
    }
    return defaultValue;
}

// Helper: Extract ULONGLONG from JSON
ULONGLONG ExtractJsonULongLong(const std::string& json, const std::string& key, ULONGLONG defaultValue = 0) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return defaultValue;
    
    pos = json.find(':', pos);
    if (pos == std::string::npos) return defaultValue;
    
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    
    size_t endPos = pos;
    while (endPos < json.length() && 
           (json[endPos] >= '0' && json[endPos] <= '9')) endPos++;
    
    if (endPos > pos) {
        return std::stoull(json.substr(pos, endPos - pos));
    }
    return defaultValue;
}

// Helper: Extract boolean from JSON
bool ExtractJsonBool(const std::string& json, const std::string& key, bool defaultValue = false) {
    std::string searchKey = "\"" + key + "\"";
    size_t pos = json.find(searchKey);
    if (pos == std::string::npos) return defaultValue;
    
    pos = json.find(':', pos);
    if (pos == std::string::npos) return defaultValue;
    
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    
    if (pos < json.length() && json[pos] == 't') {
        // Check for "true"
        if (json.substr(pos, 4) == "true") return true;
    } else if (pos < json.length() && json[pos] == 'f') {
        // Check for "false"
        if (json.substr(pos, 5) == "false") return false;
    }
    
    return defaultValue;
}

// Enable backup privilege for volume access
bool EnableBackupPrivilege() {
    HANDLE hToken = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) {
        return false;
    }
    
    TOKEN_PRIVILEGES tp = {};
    LUID luid = {};
    if (!LookupPrivilegeValueW(nullptr, L"SeBackupPrivilege", &luid)) {
        CloseHandle(hToken);
        return false;
    }
    
    tp.PrivilegeCount = 1;
    tp.Privileges[0].Luid = luid;
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    
    bool result = AdjustTokenPrivileges(hToken, FALSE, &tp, 0, nullptr, nullptr) != FALSE;
    CloseHandle(hToken);
    return result;
}

// Open volume handle
HANDLE OpenVolume(const std::wstring& volumePath) {
    std::wstring volumeName = L"\\\\.\\" + volumePath;
    if (volumeName.back() != L':') {
        volumeName += L":";
    }
    
    HANDLE hVolume = CreateFileW(
        volumeName.c_str(),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        nullptr
    );
    
    return hVolume;
}

// Get NTFS volume data (using Windows-defined structure)
bool GetNtfsVolumeData(HANDLE hVolume, ::NTFS_VOLUME_DATA_BUFFER& volumeData) {
    DWORD bytesReturned = 0;
    return DeviceIoControl(
        hVolume,
        FSCTL_GET_NTFS_VOLUME_DATA,
        nullptr,
        0,
        &volumeData,
        sizeof(volumeData),
        &bytesReturned,
        nullptr
    ) != FALSE;
}

// Read MFT record from volume using LCN (Logical Cluster Number)
bool ReadMftRecordFromVolume(HANDLE hVolume, ULONGLONG mftStartLcn, DWORD bytesPerCluster, ULONGLONG recordNumber, DWORD recordSize, std::vector<BYTE>& buffer) {
    buffer.resize(recordSize);
    
    // Calculate offset in bytes
    ULONGLONG recordOffsetInBytes = recordNumber * recordSize;
    ULONGLONG clusterOffset = recordOffsetInBytes / bytesPerCluster;
    ULONGLONG byteOffsetInCluster = recordOffsetInBytes % bytesPerCluster;
    
    // Calculate absolute LCN
    ULONGLONG targetLcn = mftStartLcn + clusterOffset;
    
    // Seek to the cluster
    LARGE_INTEGER seekPos = {};
    seekPos.QuadPart = targetLcn * bytesPerCluster + byteOffsetInCluster;
    
    if (SetFilePointerEx(hVolume, seekPos, nullptr, FILE_BEGIN) == FALSE) {
        return false;
    }
    
    // Read the record
    DWORD bytesRead = 0;
    if (!ReadFile(hVolume, buffer.data(), recordSize, &bytesRead, nullptr)) {
        return false;
    }
    
    return bytesRead == recordSize;
}

// Structure to hold all file metadata from MFT
struct FileMetadata {
    std::wstring fileName;
    std::wstring shortFileName;  // 8.3 name if available
    ULONGLONG parentDir;
    ULONGLONG fileSize;
    ULONGLONG allocatedSize;
    ULONGLONG creationTime;
    ULONGLONG modificationTime;
    ULONGLONG accessTime;
    ULONGLONG mftModificationTime;
    DWORD fileFlags;
    DWORD ownerId;
    DWORD securityId;
    ULONGLONG usn;
    bool hasStandardInfo;
};

// Parse $STANDARD_INFORMATION attribute
bool ParseStandardInformation(const BYTE* record, DWORD recordSize, FileMetadata& metadata) {
    const MFT_RECORD_HEADER* header = reinterpret_cast<const MFT_RECORD_HEADER*>(record);
    if (header->Signature != MFT_SIGNATURE) {
        return false;
    }
    
    const BYTE* attr = record + header->AttributeOffset;
    const BYTE* end = record + recordSize;
    
    while (attr < end - sizeof(ATTRIBUTE_HEADER)) {
        const ATTRIBUTE_HEADER* attrHeader = reinterpret_cast<const ATTRIBUTE_HEADER*>(attr);
        
        if (attrHeader->Type == MFT_ATTR_END) {
            break;
        }
        
        if (attrHeader->Length == 0 || attrHeader->Length > (end - attr)) {
            break;
        }
        
        if (attrHeader->Type == MFT_ATTR_STANDARD_INFORMATION && attrHeader->NonResident == 0) {
            const RESIDENT_ATTRIBUTE* resident = reinterpret_cast<const RESIDENT_ATTRIBUTE*>(attr);
            if (resident->ValueOffset + resident->ValueLength > attrHeader->Length) {
                attr += attrHeader->Length;
                continue;
            }
            
            const BYTE* value = attr + resident->ValueOffset;
            const STANDARD_INFORMATION_ATTRIBUTE* stdInfo = reinterpret_cast<const STANDARD_INFORMATION_ATTRIBUTE*>(value);
            
            // Use $STANDARD_INFORMATION timestamps (more accurate)
            metadata.creationTime = stdInfo->CreationTime;
            metadata.modificationTime = stdInfo->ModificationTime;
            metadata.accessTime = stdInfo->AccessTime;
            metadata.mftModificationTime = stdInfo->MftModificationTime;
            metadata.ownerId = stdInfo->OwnerId;
            metadata.securityId = stdInfo->SecurityId;
            metadata.usn = stdInfo->Usn;
            metadata.hasStandardInfo = true;
            
            return true;
        }
        
        attr += attrHeader->Length;
    }
    
    return false;
}

// Parse FILE_NAME attribute(s) from MFT record - supports multiple (long + short names)
bool ParseFileNameAttribute(const BYTE* record, DWORD recordSize, FileMetadata& metadata) {
    const MFT_RECORD_HEADER* header = reinterpret_cast<const MFT_RECORD_HEADER*>(record);
    if (header->Signature != MFT_SIGNATURE) {
        return false;
    }
    
    // Check if record is in use (skip deleted records)
    if (!(header->Flags & 0x0001)) {
        return false;  // Record not in use
    }
    
    const BYTE* attr = record + header->AttributeOffset;
    const BYTE* end = record + recordSize;
    bool foundAny = false;
    
    while (attr < end - sizeof(ATTRIBUTE_HEADER)) {
        const ATTRIBUTE_HEADER* attrHeader = reinterpret_cast<const ATTRIBUTE_HEADER*>(attr);
        
        if (attrHeader->Type == MFT_ATTR_END) {
            break;
        }
        
        if (attrHeader->Length == 0 || attrHeader->Length > (end - attr)) {
            break;
        }
        
        if (attrHeader->Type == MFT_ATTR_FILE_NAME && attrHeader->NonResident == 0) {
            const RESIDENT_ATTRIBUTE* resident = reinterpret_cast<const RESIDENT_ATTRIBUTE*>(attr);
            if (resident->ValueOffset + resident->ValueLength > attrHeader->Length) {
                attr += attrHeader->Length;
                continue;
            }
            
            const BYTE* value = attr + resident->ValueOffset;
            const FILE_NAME_ATTRIBUTE* fileNameAttr = reinterpret_cast<const FILE_NAME_ATTRIBUTE*>(value);
            
            if (fileNameAttr->NameLength > 0 && fileNameAttr->NameLength < 256) {
                std::wstring name;
                name.assign(fileNameAttr->Name, fileNameAttr->NameLength);
                
                // NameType: 0=POSIX, 1=Win32, 2=DOS, 3=Win32+DOS
                if (fileNameAttr->NameType == 1 || fileNameAttr->NameType == 3) {
                    // Win32 name (long name)
                    metadata.fileName = name;
                    metadata.parentDir = fileNameAttr->ParentDirectory;
                    metadata.fileSize = fileNameAttr->RealSize;
                    metadata.allocatedSize = fileNameAttr->AllocatedSize;
                    metadata.fileFlags = fileNameAttr->Flags;
                    
                    // Use $FILE_NAME timestamps if $STANDARD_INFORMATION not available
                    if (!metadata.hasStandardInfo) {
                        metadata.creationTime = fileNameAttr->CreationTime;
                        metadata.modificationTime = fileNameAttr->ModificationTime;
                        metadata.accessTime = fileNameAttr->AccessTime;
                        metadata.mftModificationTime = fileNameAttr->MftModificationTime;
                    }
                    
                    foundAny = true;
                } else if (fileNameAttr->NameType == 2 || fileNameAttr->NameType == 3) {
                    // DOS name (8.3 short name)
                    metadata.shortFileName = name;
                }
            }
        }
        
        attr += attrHeader->Length;
    }
    
    return foundAny;
}

// Check if file matches filter criteria
bool MatchesFilters(const FileMetadata& metadata, 
                    ULONGLONG minSize, ULONGLONG maxSize,
                    ULONGLONG createdAfter, ULONGLONG createdBefore,
                    ULONGLONG modifiedAfter, ULONGLONG modifiedBefore,
                    ULONGLONG accessedAfter, ULONGLONG accessedBefore,
                    bool includeDirectories, bool includeReadonly, bool includeHidden,
                    bool includeSystem, bool includeCompressed, bool includeEncrypted) {
    
    // Size filter
    if (minSize > 0 && metadata.fileSize < minSize) return false;
    if (maxSize > 0 && metadata.fileSize > maxSize) return false;
    
    // Directory filter
    bool isDirectory = (metadata.fileFlags & FILE_ATTRIBUTE_DIRECTORY) != 0;
    if (isDirectory && !includeDirectories) return false;
    
    // Timestamp filters
    if (createdAfter > 0 && metadata.creationTime < createdAfter) return false;
    if (createdBefore > 0 && metadata.creationTime > createdBefore) return false;
    if (modifiedAfter > 0 && metadata.modificationTime < modifiedAfter) return false;
    if (modifiedBefore > 0 && metadata.modificationTime > modifiedBefore) return false;
    if (accessedAfter > 0 && metadata.accessTime < accessedAfter) return false;
    if (accessedBefore > 0 && metadata.accessTime > accessedBefore) return false;
    
    // File attribute filters
    bool isReadonly = (metadata.fileFlags & FILE_ATTRIBUTE_READONLY) != 0;
    bool isHidden = (metadata.fileFlags & FILE_ATTRIBUTE_HIDDEN) != 0;
    bool isSystem = (metadata.fileFlags & FILE_ATTRIBUTE_SYSTEM) != 0;
    bool isCompressed = (metadata.fileFlags & FILE_ATTRIBUTE_COMPRESSED) != 0;
    bool isEncrypted = (metadata.fileFlags & FILE_ATTRIBUTE_ENCRYPTED) != 0;
    
    if (isReadonly && !includeReadonly) return false;
    if (isHidden && !includeHidden) return false;
    if (isSystem && !includeSystem) return false;
    if (isCompressed && !includeCompressed) return false;
    if (isEncrypted && !includeEncrypted) return false;
    
    return true;
}

// Helper function for single pattern matching (defined before MatchPattern)
static bool MatchSinglePattern(const std::wstring& name, const std::wstring& pat) {
    if (pat.empty()) return true;
    if (name.empty() && pat != L"*") return false;
    
    std::wstring lowerPattern = pat;
    std::transform(lowerPattern.begin(), lowerPattern.end(), lowerPattern.begin(), ::towlower);
    
    std::wstring lowerName = name;
    std::transform(lowerName.begin(), lowerName.end(), lowerName.begin(), ::towlower);
    
    // Simple glob matching: * and ?
    size_t patternPos = 0;
    size_t namePos = 0;
    
    while (patternPos < lowerPattern.length() && namePos < lowerName.length()) {
        if (lowerPattern[patternPos] == L'*') {
            patternPos++;
            // If * is at the end, match everything
            if (patternPos >= lowerPattern.length()) return true;
            
            // Try to match the rest of the pattern at each position in the name
            while (namePos <= lowerName.length()) {
                if (MatchSinglePattern(lowerName.substr(namePos), lowerPattern.substr(patternPos))) {
                    return true;
                }
                namePos++;
            }
            return false;
        } else if (lowerPattern[patternPos] == L'?') {
            patternPos++;
            namePos++;
        } else if (lowerPattern[patternPos] == lowerName[namePos]) {
            patternPos++;
            namePos++;
        } else {
            return false;
        }
    }
    
    // Skip trailing * in pattern
    while (patternPos < lowerPattern.length() && lowerPattern[patternPos] == L'*') {
        patternPos++;
    }
    
    // Both must be exhausted
    return patternPos >= lowerPattern.length() && namePos >= lowerName.length();
}

// Match pattern against filename (simple glob matching) - also checks short name
bool MatchPattern(const std::wstring& fileName, const std::wstring& shortFileName, const std::wstring& pattern) {
    if (pattern.empty()) return true;
    
    // Try matching against long name first
    if (MatchSinglePattern(fileName, pattern)) return true;
    
    // Try matching against short name if available
    if (!shortFileName.empty() && MatchSinglePattern(shortFileName, pattern)) return true;
    
    return false;
}

// Escape JSON string
std::string EscapeJsonString(const std::string& str) {
    std::string escaped;
    escaped.reserve(str.length() * 2);
    
    for (char c : str) {
        switch (c) {
            case '"': escaped += "\\\""; break;
            case '\\': escaped += "\\\\"; break;
            case '\b': escaped += "\\b"; break;
            case '\f': escaped += "\\f"; break;
            case '\n': escaped += "\\n"; break;
            case '\r': escaped += "\\r"; break;
            case '\t': escaped += "\\t"; break;
            default:
                if (c >= 0 && c < 32) {
                    char buf[7];
                    sprintf_s(buf, sizeof(buf), "\\u%04x", static_cast<unsigned char>(c));
                    escaped += buf;
                } else {
                    escaped += c;
                }
                break;
        }
    }
    
    return escaped;
}

}  // namespace

// Main search function - DIRECT MFT ACCESS - NO TREE WALKING!
std::string HandleSearchRequestImpl(const std::string& requestJson) {
    HANDLE hVolume = INVALID_HANDLE_VALUE;
    
    try {
        // Parse request - basic parameters
        std::string pattern = ExtractJsonString(requestJson, "pattern");
        std::string directory = ExtractJsonString(requestJson, "directory");
        int maxResults = ExtractJsonInt(requestJson, "max_results", 100);
        
        // Parse pagination parameters
        std::string paginationMode = ExtractJsonString(requestJson, "pagination_mode");
        int page = ExtractJsonInt(requestJson, "page", 1);
        int pageSize = ExtractJsonInt(requestJson, "page_size", 1000);
        
        // Validate pagination parameters
        // Default to "none" if pagination_mode is empty or not provided
        bool usePagination = (!paginationMode.empty() && paginationMode == "offset");
        if (usePagination) {
            if (page < 1) page = 1;
            if (pageSize < 1) pageSize = 1000;
            if (pageSize > 100000) pageSize = 100000;  // Cap at 100k per page
        }
        
        // Sanity check: Warn about dangerous patterns that match everything
        bool isDangerousPattern = (pattern == "*.*" || pattern == "*" || pattern == ".*");
        if (isDangerousPattern && maxResults == 0) {
            std::wstringstream warnMsg;
            warnMsg << L"WARNING: Unlimited search requested with pattern '" 
                    << std::wstring(pattern.begin(), pattern.end()) 
                    << L"' which matches ALL files. This may return millions of results.";
            LogServiceEvent(EVENTLOG_WARNING_TYPE, warnMsg.str(), 0);
        }
        
        // Handle unlimited searches (maxResults == 0)
        // Apply safety limit to prevent memory exhaustion
        bool isUnlimited = (maxResults == 0);
        if (isUnlimited) {
            maxResults = MAX_SAFE_RESULTS;
            std::wstringstream infoMsg;
            infoMsg << L"Unlimited search requested. Applying safety limit of " 
                    << MAX_SAFE_RESULTS << L" results.";
            LogServiceEvent(EVENTLOG_INFORMATION_TYPE, infoMsg.str(), 0);
        }
        
        // Additional sanity check: Warn if pattern is too broad and maxResults is very large
        if (maxResults > WARN_RESULTS_THRESHOLD && (pattern.find('*') != std::string::npos || pattern.find('?') != std::string::npos)) {
            std::wstringstream warnMsg;
            warnMsg << L"Large result limit (" << maxResults 
                    << L") requested with wildcard pattern. This may take a long time.";
            LogServiceEvent(EVENTLOG_WARNING_TYPE, warnMsg.str(), 0);
        }
        
        // Parse filter parameters
        ULONGLONG minSize = ExtractJsonULongLong(requestJson, "min_size", 0);
        ULONGLONG maxSize = ExtractJsonULongLong(requestJson, "max_size", 0);
        ULONGLONG createdAfter = ExtractJsonULongLong(requestJson, "created_after", 0);
        ULONGLONG createdBefore = ExtractJsonULongLong(requestJson, "created_before", 0);
        ULONGLONG modifiedAfter = ExtractJsonULongLong(requestJson, "modified_after", 0);
        ULONGLONG modifiedBefore = ExtractJsonULongLong(requestJson, "modified_before", 0);
        ULONGLONG accessedAfter = ExtractJsonULongLong(requestJson, "accessed_after", 0);
        ULONGLONG accessedBefore = ExtractJsonULongLong(requestJson, "accessed_before", 0);
        bool includeDirectories = ExtractJsonBool(requestJson, "include_directories", false);
        bool includeReadonly = ExtractJsonBool(requestJson, "include_readonly", true);
        bool includeHidden = ExtractJsonBool(requestJson, "include_hidden", false);
        bool includeSystem = ExtractJsonBool(requestJson, "include_system", false);
        bool includeCompressed = ExtractJsonBool(requestJson, "include_compressed", true);
        bool includeEncrypted = ExtractJsonBool(requestJson, "include_encrypted", true);
        
        if (pattern.empty()) {
            return "{\"success\":false,\"error\":\"Pattern is required\"}";
        }
        
        // Determine volume from directory
        // Extract drive letter from directory (handles "D:", "D:\\", "d:", etc.)
        std::wstring volumePath = L"C:";
        if (!directory.empty()) {
            if (directory.length() >= 2 && directory[1] == ':') {
                // Extract drive letter and convert to uppercase
                char driveLetter = directory[0];
                if (driveLetter >= 'a' && driveLetter <= 'z') {
                    driveLetter = driveLetter - 'a' + 'A';  // Convert to uppercase
                }
                volumePath = std::wstring(1, static_cast<wchar_t>(driveLetter)) + L":";
            }
        }
        
        // Convert pattern to wide string
        std::wstring wpattern(pattern.begin(), pattern.end());
        
        // Enable backup privilege
        EnableBackupPrivilege();
        
        // Open volume
        hVolume = OpenVolume(volumePath);
        if (hVolume == INVALID_HANDLE_VALUE) {
            DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"Failed to open volume " << volumePath << L" with error " << error;
            LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
            return "{\"success\":false,\"error\":\"Failed to open volume\"}";
        }
        
        // Get volume data
        ::NTFS_VOLUME_DATA_BUFFER volumeData = {};
        if (!GetNtfsVolumeData(hVolume, volumeData)) {
            DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"Failed to get NTFS volume data with error " << error;
            LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
            CloseHandle(hVolume);
            return "{\"success\":false,\"error\":\"Failed to get volume data\"}";
        }
        
        DWORD recordSize = volumeData.BytesPerFileRecordSegment;
        if (recordSize == 0) {
            recordSize = 1024;  // Default
        }
        
        DWORD bytesPerCluster = volumeData.BytesPerCluster;
        if (bytesPerCluster == 0) {
            bytesPerCluster = 4096;  // Default
        }
        
        ULONGLONG mftStartLcn = volumeData.MftStartLcn.QuadPart;
        
        // Get number of CPU cores for multithreading
        SYSTEM_INFO sysInfo = {};
        GetSystemInfo(&sysInfo);
        DWORD numThreads = sysInfo.dwNumberOfProcessors;
        if (numThreads < 1) numThreads = 1;
        if (numThreads > 16) numThreads = 16;  // Cap at 16 threads to avoid overhead
        
        std::wstringstream logMsg;
        logMsg << L"Starting multithreaded MFT search with " << numThreads << L" threads";
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, logMsg.str());
        
        // Shared data structures for multithreaded search
        std::vector<std::string> results;
        std::mutex resultsMutex;
        std::atomic<ULONGLONG> recordsRead(0);
        std::atomic<bool> shouldStop(false);
        
        // Search parameters structure for threads
        struct SearchParams {
            std::wstring volumePath;
            ULONGLONG mftStartLcn;
            DWORD recordSize;
            DWORD bytesPerCluster;
            ULONGLONG startRecord;
            ULONGLONG endRecord;
            std::wstring pattern;
            ULONGLONG minSize, maxSize;
            ULONGLONG createdAfter, createdBefore;
            ULONGLONG modifiedAfter, modifiedBefore;
            ULONGLONG accessedAfter, accessedBefore;
            bool includeDirectories, includeReadonly, includeHidden;
            bool includeSystem, includeCompressed, includeEncrypted;
            int maxResults;
            std::vector<std::string>* results;
            std::mutex* resultsMutex;
            std::atomic<ULONGLONG>* recordsRead;
            std::atomic<bool>* shouldStop;
        };
        
        // Estimate MFT size (scan first 1000 records to find end)
        ULONGLONG estimatedMftSize = 1000000;  // Default estimate
        ULONGLONG testRecord = 5;
        ULONGLONG consecutiveFailures = 0;
        const ULONGLONG maxConsecutiveFailures = 1000;
        std::vector<BYTE> testBuffer(recordSize);
        
        // Quick scan to estimate MFT size
        for (ULONGLONG i = 0; i < 10000 && consecutiveFailures < 100; i++) {
            if (ReadMftRecordFromVolume(hVolume, mftStartLcn, bytesPerCluster, testRecord, recordSize, testBuffer)) {
                consecutiveFailures = 0;
                estimatedMftSize = testRecord + 10000;  // Update estimate
            } else {
                consecutiveFailures++;
            }
            testRecord += 1000;  // Sample every 1000th record
        }
        
        // Divide MFT into chunks for each thread
        ULONGLONG startRecord = 5;  // First user file
        ULONGLONG recordsPerThread = (estimatedMftSize - startRecord) / numThreads;
        if (recordsPerThread < 1000) recordsPerThread = 1000;  // Minimum chunk size
        
        // Worker thread function - capture maxConsecutiveFailures
        auto workerThread = [maxConsecutiveFailures](const SearchParams& params) {
            // Each thread opens its own volume handle
            HANDLE threadVolume = OpenVolume(params.volumePath);
            if (threadVolume == INVALID_HANDLE_VALUE) {
                return;  // Thread can't proceed without volume handle
            }
            
            std::vector<BYTE> recordBuffer(params.recordSize);
            ULONGLONG localRecordsRead = 0;
            ULONGLONG localConsecutiveFailures = 0;
            
            for (ULONGLONG recordNumber = params.startRecord; 
                 recordNumber < params.endRecord && !(*params.shouldStop); 
                 recordNumber++) {
                
                // Check if we have enough results
                // Skip check if maxResults is 0 (unlimited) - but we've already capped it at MAX_SAFE_RESULTS
                {
                    std::lock_guard<std::mutex> lock(*params.resultsMutex);
                    if (params.maxResults > 0 && params.results->size() >= static_cast<size_t>(params.maxResults)) {
                        *params.shouldStop = true;
                        break;
                    }
                    
                    // Warn if approaching safety limit
                    if (params.results->size() == WARN_RESULTS_THRESHOLD) {
                        std::wstringstream warnMsg;
                        warnMsg << L"Search results approaching safety limit: " 
                                << params.results->size() << L" files found so far.";
                        LogServiceEvent(EVENTLOG_WARNING_TYPE, warnMsg.str(), 0);
                    }
                }
                
                if (!ReadMftRecordFromVolume(threadVolume, params.mftStartLcn, params.bytesPerCluster, 
                                            recordNumber, params.recordSize, recordBuffer)) {
                    localConsecutiveFailures++;
                    if (localConsecutiveFailures > maxConsecutiveFailures) {
                        break;  // End of MFT for this chunk
                    }
                    continue;
                }
                
                localConsecutiveFailures = 0;
                localRecordsRead++;
                (*params.recordsRead)++;
                
                // Parse record
                FileMetadata metadata = {};
                metadata.hasStandardInfo = false;
                ParseStandardInformation(recordBuffer.data(), params.recordSize, metadata);
                
                if (ParseFileNameAttribute(recordBuffer.data(), params.recordSize, metadata)) {
                    // Apply filters
                    if (!MatchesFilters(metadata, params.minSize, params.maxSize,
                                       params.createdAfter, params.createdBefore,
                                       params.modifiedAfter, params.modifiedBefore,
                                       params.accessedAfter, params.accessedBefore,
                                       params.includeDirectories, params.includeReadonly, params.includeHidden,
                                       params.includeSystem, params.includeCompressed, params.includeEncrypted)) {
                        continue;
                    }
                    
                    // Match pattern
                    if (MatchPattern(metadata.fileName, metadata.shortFileName, params.pattern)) {
                        // Convert to UTF-8
                        int utf8Size = WideCharToMultiByte(CP_UTF8, 0, metadata.fileName.c_str(), -1, nullptr, 0, nullptr, nullptr);
                        std::string utf8FileName(utf8Size - 1, '\0');
                        WideCharToMultiByte(CP_UTF8, 0, metadata.fileName.c_str(), -1, &utf8FileName[0], utf8Size, nullptr, nullptr);
                        
                        std::string utf8ShortFileName;
                        if (!metadata.shortFileName.empty()) {
                            int shortSize = WideCharToMultiByte(CP_UTF8, 0, metadata.shortFileName.c_str(), -1, nullptr, 0, nullptr, nullptr);
                            utf8ShortFileName = std::string(shortSize - 1, '\0');
                            WideCharToMultiByte(CP_UTF8, 0, metadata.shortFileName.c_str(), -1, &utf8ShortFileName[0], shortSize, nullptr, nullptr);
                        }
                        
                        // Build result JSON
                        std::ostringstream result;
                        result << "{\"path\":\"" << EscapeJsonString(utf8FileName) << "\","
                               << "\"name\":\"" << EscapeJsonString(utf8FileName) << "\"";
                        
                        if (!utf8ShortFileName.empty()) {
                            result << ",\"short_name\":\"" << EscapeJsonString(utf8ShortFileName) << "\"";
                        }
                        
                        bool isDirectory = (metadata.fileFlags & FILE_ATTRIBUTE_DIRECTORY) != 0;
                        bool isReadonly = (metadata.fileFlags & FILE_ATTRIBUTE_READONLY) != 0;
                        bool isHidden = (metadata.fileFlags & FILE_ATTRIBUTE_HIDDEN) != 0;
                        bool isSystem = (metadata.fileFlags & FILE_ATTRIBUTE_SYSTEM) != 0;
                        bool isCompressed = (metadata.fileFlags & FILE_ATTRIBUTE_COMPRESSED) != 0;
                        bool isEncrypted = (metadata.fileFlags & FILE_ATTRIBUTE_ENCRYPTED) != 0;
                        
                        result << ",\"size\":" << metadata.fileSize
                               << ",\"allocated_size\":" << metadata.allocatedSize
                               << ",\"created\":" << metadata.creationTime
                               << ",\"modified\":" << metadata.modificationTime
                               << ",\"accessed\":" << metadata.accessTime
                               << ",\"mft_modified\":" << metadata.mftModificationTime
                               << ",\"parent_dir\":" << metadata.parentDir
                               << ",\"flags\":" << metadata.fileFlags
                               << ",\"is_directory\":" << (isDirectory ? "true" : "false")
                               << ",\"is_readonly\":" << (isReadonly ? "true" : "false")
                               << ",\"is_hidden\":" << (isHidden ? "true" : "false")
                               << ",\"is_system\":" << (isSystem ? "true" : "false")
                               << ",\"is_compressed\":" << (isCompressed ? "true" : "false")
                               << ",\"is_encrypted\":" << (isEncrypted ? "true" : "false");
                        
                        if (metadata.hasStandardInfo) {
                            result << ",\"owner_id\":" << metadata.ownerId
                                   << ",\"security_id\":" << metadata.securityId
                                   << ",\"usn\":" << metadata.usn;
                        }
                        
                        result << "}";
                        
                        // Thread-safe result collection
                        {
                            std::lock_guard<std::mutex> lock(*params.resultsMutex);
                            // Always add result if we haven't hit the limit
                            // (maxResults is already capped at MAX_SAFE_RESULTS for unlimited searches)
                            if (params.results->size() < static_cast<size_t>(params.maxResults)) {
                                params.results->push_back(result.str());
                                
                                // Check if we've hit the limit
                                if (params.results->size() >= static_cast<size_t>(params.maxResults)) {
                                    *params.shouldStop = true;
                                }
                                
                                // Warn if approaching safety limit
                                if (params.results->size() == WARN_RESULTS_THRESHOLD) {
                                    std::wstringstream warnMsg;
                                    warnMsg << L"Search results approaching safety limit: " 
                                            << params.results->size() << L" files found so far.";
                                    LogServiceEvent(EVENTLOG_WARNING_TYPE, warnMsg.str(), 0);
                                }
                                
                                // Stop if we hit the absolute safety limit (extra safety check)
                                if (params.results->size() >= MAX_SAFE_RESULTS) {
                                    std::wstringstream errorMsg;
                                    errorMsg << L"Search stopped at safety limit: " 
                                            << MAX_SAFE_RESULTS << L" results. Use a more specific pattern.";
                                    LogServiceEvent(EVENTLOG_WARNING_TYPE, errorMsg.str(), 0);
                                    *params.shouldStop = true;
                                }
                            }
                        }
                    }
                }
            }
            
            CloseHandle(threadVolume);
        };
        
        // Launch worker threads
        std::vector<std::thread> threads;
        std::vector<SearchParams> threadParams(numThreads);
        
        for (DWORD i = 0; i < numThreads; i++) {
            threadParams[i] = {
                volumePath, mftStartLcn, recordSize, bytesPerCluster,
                startRecord + (i * recordsPerThread),
                (i == numThreads - 1) ? estimatedMftSize : (startRecord + ((i + 1) * recordsPerThread)),
                wpattern, minSize, maxSize,
                createdAfter, createdBefore, modifiedAfter, modifiedBefore,
                accessedAfter, accessedBefore,
                includeDirectories, includeReadonly, includeHidden,
                includeSystem, includeCompressed, includeEncrypted,
                maxResults, &results, &resultsMutex, &recordsRead, &shouldStop
            };
            
            threads.emplace_back(workerThread, threadParams[i]);
        }
        
        // Wait for all threads to complete
        for (auto& thread : threads) {
            thread.join();
        }
        
        CloseHandle(hVolume);
        
        // Apply pagination if requested
        size_t totalResults = results.size();
        size_t startIndex = 0;
        size_t endIndex = totalResults;
        
        if (usePagination) {
            startIndex = static_cast<size_t>((page - 1) * pageSize);
            endIndex = startIndex + static_cast<size_t>(pageSize);
            
            // Clamp to available results
            if (startIndex > totalResults) {
                startIndex = totalResults;
                endIndex = totalResults;
            }
            if (endIndex > totalResults) {
                endIndex = totalResults;
            }
        }
        
        // Build response with pagination metadata
        std::ostringstream response;
        response << "{\"success\":true,\"results\":[";
        
        // Output only the requested page
        bool firstResult = true;
        for (size_t i = startIndex; i < endIndex; i++) {
            if (!firstResult) response << ",";
            response << results[i];
            firstResult = false;
        }
        
        size_t pageResultCount = (endIndex > startIndex) ? (endIndex - startIndex) : 0;
        response << "],\"count\":" << pageResultCount;
        
        // Add pagination metadata
        if (usePagination) {
            int totalPages = (totalResults > 0) ? static_cast<int>((totalResults - 1) / pageSize + 1) : 0;
            bool hasNext = (page < totalPages);
            bool hasPrevious = (page > 1);
            
            response << ",\"pagination\":{"
                     << "\"mode\":\"offset\","
                     << "\"page\":" << page << ","
                     << "\"page_size\":" << pageSize << ","
                     << "\"total_pages\":" << totalPages << ","
                     << "\"total_results\":" << totalResults << ","
                     << "\"has_next\":" << (hasNext ? "true" : "false") << ","
                     << "\"has_previous\":" << (hasPrevious ? "true" : "false")
                     << "}";
        } else {
            response << ",\"pagination\":null";
        }
        
        response << "}";
        
        std::wstringstream finalLogMsg;
        if (usePagination) {
            finalLogMsg << L"Multithreaded MFT search completed (page " << page << "): " 
                       << pageResultCount << L" results (page " << page << " of " 
                       << ((totalResults > 0) ? ((totalResults - 1) / pageSize + 1) : 0) 
                       << ") from " << totalResults << L" total results, " 
                       << recordsRead.load() << L" records scanned using " << numThreads << L" threads";
        } else {
            finalLogMsg << L"Multithreaded MFT search completed: " << results.size() << L" results from " 
                       << recordsRead.load() << L" records scanned using " << numThreads << L" threads";
        }
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, finalLogMsg.str());
        
        return response.str();
        
    } catch (const std::exception& e) {
        if (hVolume != INVALID_HANDLE_VALUE) CloseHandle(hVolume);
        
        std::wstringstream ss;
        ss << L"Exception in HandleSearchRequest: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), 0);
        return "{\"success\":false,\"error\":\"Internal error processing search request\"}";
    } catch (...) {
        if (hVolume != INVALID_HANDLE_VALUE) CloseHandle(hVolume);
        
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in HandleSearchRequest", 0);
        return "{\"success\":false,\"error\":\"Internal error processing search request\"}";
    }
}
