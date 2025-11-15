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

namespace {

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
#pragma pack(pop)

// Constants (use existing Windows definitions where possible)
static const DWORD MFT_ATTR_FILE_NAME = 0x30;
static const DWORD MFT_ATTR_END = 0xFFFFFFFF;
static const DWORD MFT_SIGNATURE = 0x454C4946;  // "FILE"

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

// Parse FILE_NAME attribute from MFT record
bool ParseFileNameAttribute(const BYTE* record, DWORD recordSize, std::wstring& fileName, ULONGLONG& parentDir, ULONGLONG& fileSize, ULONGLONG& modifiedTime, DWORD& fileFlags) {
    const MFT_RECORD_HEADER* header = reinterpret_cast<const MFT_RECORD_HEADER*>(record);
    if (header->Signature != MFT_SIGNATURE) {
        return false;
    }
    
    // Check if record is in use
    if (header->Flags & 0x0001) {  // Record is in use
        // Skip deleted records
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
        
        if (attrHeader->Type == MFT_ATTR_FILE_NAME && attrHeader->NonResident == 0) {
            const RESIDENT_ATTRIBUTE* resident = reinterpret_cast<const RESIDENT_ATTRIBUTE*>(attr);
            if (resident->ValueOffset + resident->ValueLength > attrHeader->Length) {
                attr += attrHeader->Length;
                continue;
            }
            
            const BYTE* value = attr + resident->ValueOffset;
            const FILE_NAME_ATTRIBUTE* fileNameAttr = reinterpret_cast<const FILE_NAME_ATTRIBUTE*>(value);
            
            if (fileNameAttr->NameLength > 0 && fileNameAttr->NameLength < 256) {
                parentDir = fileNameAttr->ParentDirectory;
                fileSize = fileNameAttr->RealSize;
                modifiedTime = fileNameAttr->ModificationTime;
                fileFlags = fileNameAttr->Flags;
                fileName.assign(fileNameAttr->Name, fileNameAttr->NameLength);
                return true;
            }
        }
        
        attr += attrHeader->Length;
    }
    
    return false;
}

// Match pattern against filename (simple glob matching)
bool MatchPattern(const std::wstring& fileName, const std::wstring& pattern) {
    if (pattern.empty()) return true;
    
    // Convert pattern to lowercase for case-insensitive matching
    std::wstring lowerPattern = pattern;
    std::transform(lowerPattern.begin(), lowerPattern.end(), lowerPattern.begin(), ::towlower);
    
    std::wstring lowerFileName = fileName;
    std::transform(lowerFileName.begin(), lowerFileName.end(), lowerFileName.begin(), ::towlower);
    
    // Simple glob matching: * and ?
    size_t patternPos = 0;
    size_t namePos = 0;
    
    while (patternPos < lowerPattern.length() && namePos < lowerFileName.length()) {
        if (lowerPattern[patternPos] == L'*') {
            // Match zero or more characters
            patternPos++;
            if (patternPos >= lowerPattern.length()) {
                return true;  // * at end matches everything
            }
            
            // Try to match the rest of the pattern
            while (namePos < lowerFileName.length()) {
                if (MatchPattern(lowerFileName.substr(namePos), lowerPattern.substr(patternPos))) {
                    return true;
                }
                namePos++;
            }
            return false;
        } else if (lowerPattern[patternPos] == L'?') {
            // Match single character
            patternPos++;
            namePos++;
        } else if (lowerPattern[patternPos] == lowerFileName[namePos]) {
            patternPos++;
            namePos++;
        } else {
            return false;
        }
    }
    
    // Both must be exhausted
    while (patternPos < lowerPattern.length() && lowerPattern[patternPos] == L'*') {
        patternPos++;
    }
    
    return patternPos >= lowerPattern.length() && namePos >= lowerFileName.length();
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
        // Parse request
        std::string pattern = ExtractJsonString(requestJson, "pattern");
        std::string directory = ExtractJsonString(requestJson, "directory");
        int maxResults = ExtractJsonInt(requestJson, "max_results", 100);
        
        if (pattern.empty()) {
            return "{\"success\":false,\"error\":\"Pattern is required\"}";
        }
        
        // Determine volume from directory
        std::wstring volumePath = L"C:";
        if (!directory.empty()) {
            if (directory.length() >= 2 && directory[1] == ':') {
                volumePath = std::wstring(1, directory[0]) + L":";
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
        
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Reading MFT directly from volume using LCN");
        
        // Read MFT records sequentially from volume
        std::vector<std::string> results;
        std::vector<BYTE> recordBuffer(recordSize);
        
        // Start reading from record 5 (first user file)
        // Record 0 = $MFT, Record 1 = $MFTMirr, Record 2 = $LogFile, etc.
        ULONGLONG recordNumber = 5;
        ULONGLONG recordsRead = 0;
        const ULONGLONG maxRecordsToScan = 1000000;  // Safety limit
        
        while (recordsRead < maxRecordsToScan && results.size() < static_cast<size_t>(maxResults)) {
            if (!ReadMftRecordFromVolume(hVolume, mftStartLcn, bytesPerCluster, recordNumber, recordSize, recordBuffer)) {
                // End of MFT or error - try next record
                recordNumber++;
                if (recordNumber > 100000) {  // Reasonable limit
                    break;
                }
                continue;
            }
            
            recordsRead++;
            
            // Parse record
            std::wstring fileName;
            ULONGLONG parentDir = 0;
            ULONGLONG fileSize = 0;
            ULONGLONG modifiedTime = 0;
            DWORD fileFlags = 0;
            
            if (ParseFileNameAttribute(recordBuffer.data(), recordSize, fileName, parentDir, fileSize, modifiedTime, fileFlags)) {
                // Skip directories if pattern doesn't explicitly allow them
                bool isDirectory = (fileFlags & 0x10) != 0;  // FILE_ATTRIBUTE_DIRECTORY
                if (isDirectory) {
                    recordNumber++;
                    continue;
                }
                
                // Match pattern
                if (MatchPattern(fileName, wpattern)) {
                    // Convert to UTF-8
                    int utf8Size = WideCharToMultiByte(CP_UTF8, 0, fileName.c_str(), -1, nullptr, 0, nullptr, nullptr);
                    std::string utf8FileName(utf8Size - 1, '\0');
                    WideCharToMultiByte(CP_UTF8, 0, fileName.c_str(), -1, &utf8FileName[0], utf8Size, nullptr, nullptr);
                    
                    // Build result
                    std::ostringstream result;
                    result << "{\"path\":\"" << EscapeJsonString(utf8FileName) << "\","
                           << "\"name\":\"" << EscapeJsonString(utf8FileName) << "\","
                           << "\"size\":" << fileSize << ","
                           << "\"modified\":" << modifiedTime << "}";
                    
                    results.push_back(result.str());
                }
            }
            
            recordNumber++;
        }
        
        CloseHandle(hVolume);
        
        // Build response
        std::ostringstream response;
        response << "{\"success\":true,\"results\":[";
        for (size_t i = 0; i < results.size(); i++) {
            if (i > 0) response << ",";
            response << results[i];
        }
        response << "],\"count\":" << results.size() << "}";
        
        std::wstringstream logMsg;
        logMsg << L"Direct MFT search completed: " << results.size() << L" results from " << recordsRead << L" records scanned";
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, logMsg.str());
        
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
