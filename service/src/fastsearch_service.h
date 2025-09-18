#pragma once

#ifndef FASTSEARCH_SERVICE_H
#define FASTSEARCH_SERVICE_H

// Prevent Windows SDK from defining min/max macros
#define NOMINMAX

// Define Windows version requirements
#define WINVER 0x0601          // Windows 7
#define _WIN32_WINNT 0x0601    // Windows 7
#define NTDDI_VERSION 0x06010000 // Windows 7

#define WIN32_LEAN_AND_MEAN

// Include Windows headers first
#include <windows.h>
#include <winioctl.h>
#include <ntddscsi.h>
#include <ntdddisk.h>
#include <winternl.h>
#include <sddl.h>
#include <aclapi.h>

// Then include C++ headers
#include <tchar.h>
#include <strsafe.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <algorithm>
#include <cstdint>

// Define MFT record related types
typedef unsigned char BYTE;
typedef BYTE* PBYTE;
typedef const BYTE* PCBYTE;
typedef wchar_t WCHAR;
typedef WCHAR* LPWSTR;
typedef const WCHAR* LPCWSTR;
typedef const TCHAR* LPCTSTR;

// NTFS attribute types
#define ATTRIBUTE_STANDARD_INFORMATION 0x10
#define ATTRIBUTE_ATTRIBUTE_LIST 0x20
#define ATTRIBUTE_FILE_NAME 0x30
#define ATTRIBUTE_OBJECT_ID 0x40
#define ATTRIBUTE_SECURITY_DESCRIPTOR 0x50
#define ATTRIBUTE_VOLUME_NAME 0x60
#define ATTRIBUTE_VOLUME_INFORMATION 0x70
#define ATTRIBUTE_DATA 0x80
#define ATTRIBUTE_INDEX_ROOT 0x90
#define ATTRIBUTE_INDEX_ALLOCATION 0xA0
#define ATTRIBUTE_BITMAP 0xB0

// FILE_NAME structure
typedef struct _FILE_NAME {
    ULONGLONG ParentDirectory;
    LARGE_INTEGER CreationTime;
    LARGE_INTEGER LastAccessTime;
    LARGE_INTEGER LastWriteTime;
    LARGE_INTEGER ChangeTime;
    ULONGLONG EndOfFile;
    ULONGLONG AllocationSize;
    ULONG FileAttributes;
    ULONG FileNameLength;
    ULONG EaSize;
    WCHAR FileName[1];
} FILE_NAME, *PFILE_NAME;

// Use the Windows SDK's MFT_RECORD_HEADER if available
#ifndef _NTIFS_
// Define our own if not available from the SDK
typedef struct _MFT_RECORD_HEADER {
    DWORD Signature;
    USHORT UpdateSequenceOffset;
    USHORT UpdateSequenceSize;
    ULONGLONG LogFileSequenceNumber;
    USHORT SequenceNumber;
    USHORT HardLinkCount;
    USHORT FirstAttributeOffset;
    USHORT Flags;
    ULONG UsedSize;
    ULONG AllocatedSize;
    ULONGLONG FileReferenceNumber;
    USHORT NextAttributeNumber;
    USHORT Padding;
    ULONG MFTRecordNumber;
} MFT_RECORD_HEADER, *PMFT_RECORD_HEADER;
#endif

// Use the NTFS_VOLUME_DATA_BUFFER from winioctl.h

// Service configuration
#define SVCNAME TEXT("FastSearchMCP")
#define SVC_DISPLAY_NAME TEXT("FastSearch MCP Service")
#define SVC_DESCRIPTION TEXT("Provides fast file search capabilities using MFT")
#define PIPE_NAME TEXT("\\\\.\\pipe\\FastSearchMCPService")
#define BUFSIZE 4096
#define MAX_CACHE_ENTRIES 1000000      // 1 million entries in cache
#define MAX_FILE_RECORDS 100000000     // 100 million max files
#define MAX_WORKER_THREADS 16          // Number of worker threads for parallel processing
#define MFT_READ_CHUNK_SIZE 1024       // Process 1024 records per chunk

// NTFS MFT related constants
#define MAX_PATH_LENGTH 32767
#define MAX_ATTR_SIZE 65536
#define CACHE_TTL_MS 300000  // 5 minutes

// Use Windows SDK's MFT_RECORD_HEADER and related types
#include <winioctl.h>

// NTFS attribute headers
typedef struct _ATTRIBUTE_RECORD_HEADER {
    DWORD TypeCode;
    DWORD RecordLength;
    BYTE FormCode;
    BYTE NameLength;
    WORD NameOffset;
    WORD Flags;
    WORD Instance;
    union {
        struct {
            DWORD ValueLength;
            WORD ValueOffset;
            BYTE ResidentFlags;
            BYTE Reserved;
        } Resident;
        struct {
            DWORD LowestVCN;
            DWORD HighestVCN;
            WORD MappingPairsOffset;
            WORD CompressionUnit;
            DWORD ReservedFields[5];
            LONGLONG AllocatedLength;
            LONGLONG FileSize;
            LONGLONG ValidDataLength;
        } NonResident;
    } Form;
} ATTRIBUTE_RECORD_HEADER, *PATTRIBUTE_RECORD_HEADER;
#define ATTR_VOLUME_NAME 0x60
#define ATTR_VOLUME_INFORMATION 0x70
#define ATTR_DATA 0x80
#define ATTR_INDEX_ROOT 0x90
#define ATTR_INDEX_ALLOCATION 0xA0
#define ATTR_BITMAP 0xB0

// Forward declarations
typedef struct _MFTCacheEntry MFTCacheEntry;
typedef struct _FileNameIndex FileNameIndex;
typedef struct _AttributeCacheEntry AttributeCacheEntry;

// MFT Cache Entry
struct _MFTCacheEntry {
    ULONGLONG recordNumber;
    FILETIME lastAccessTime;
    DWORD accessCount;
    PBYTE recordData;
    DWORD recordSize;
    MFTCacheEntry* next;
    MFTCacheEntry* prev;
};

// File Name Index Entry
struct _FileNameIndex {
    WCHAR fileName[MAX_PATH];
    ULONGLONG parentRecordNumber;
    ULONGLONG recordNumber;
    FileNameIndex* next;
};

// Attribute cache entry
struct _AttributeCacheEntry {
    ULONGLONG recordNumber;
    DWORD attrType;  // Changed from NTFS_ATTR_TYPE to DWORD
    DWORD instance;
    PBYTE data;
    DWORD size;
    FILETIME lastAccessTime;
    AttributeCacheEntry* next;
};

// Global cache structure
typedef struct _CacheManager {
    MFTCacheEntry** hashTable;     // Hash table for O(1) lookups
    MFTCacheEntry* lruHead;        // LRU list head
    MFTCacheEntry* lruTail;        // LRU list tail
    DWORD size;                    // Current cache size
    DWORD capacity;                // Max cache size
    CRITICAL_SECTION cs;           // Thread safety
    HANDLE hHeap;                  // Dedicated heap for cache
} CacheManager;

// Global variables
extern SERVICE_STATUS gSvcStatus;
extern SERVICE_STATUS_HANDLE gSvcStatusHandle;
extern HANDLE ghSvcStopEvent;
extern CacheManager gCache;
extern CRITICAL_SECTION gCacheCS;
extern CRITICAL_SECTION gIndexCS;
extern CRITICAL_SECTION gAttrCacheCS;
extern FileNameIndex* gFileNameIndex;
extern AttributeCacheEntry* gAttrCache;

// Worker thread context for MFT record processing
typedef struct _WORKER_THREAD_CTX {
    HANDLE hThread;         // Thread handle
    DWORD threadId;         // Thread ID
    HANDLE hStartEvent;     // Event to signal thread to start processing
    HANDLE hCompleteEvent;  // Event to signal when processing is complete
    PBYTE pBuffer;          // Pointer to buffer containing MFT records
    DWORD recordCount;      // Number of records to process
    DWORD recordSize;       // Size of each record
    ULONGLONG startRecord;  // Starting record number
    BOOL shutdown;          // Flag to indicate thread should exit
} WORKER_THREAD_CTX, *PWORKER_THREAD_CTX;

// Function declarations
// Initialization
void InitializeGlobalCS();

// Cache management
void InitializeCaches();
void CleanupCaches();
void AddToCache(ULONGLONG recordNumber, PBYTE recordData, DWORD recordSize);
PBYTE GetFromCache(ULONGLONG recordNumber, DWORD* pRecordSize);
void AddToFileIndex(ULONGLONG recordNumber, ULONGLONG parentRecordNumber, LPCWSTR fileName);
BOOL FindFileInIndex(LPCWSTR fileName, ULONGLONG* pRecordNumber);
void AddToAttributeCache(ULONGLONG recordNumber, DWORD attrType, DWORD instance, PBYTE data, DWORD size);
PBYTE GetFromAttributeCache(ULONGLONG recordNumber, DWORD attrType, DWORD instance, DWORD* pSize);
void CleanupOldCacheEntries();

// NTFS operations
BOOL EnablePrivilege(LPCTSTR pszPrivilege);
HANDLE OpenVolume(LPCTSTR pszRootPath);
BOOL GetNtfsVolumeData(HANDLE hVolume, PNTFS_VOLUME_DATA_BUFFER pVolumeData);
DWORD GetMFTRecordSize(HANDLE hVolume);
BOOL ReadMFTRecords(HANDLE hVolume, ULONGLONG startRecord, DWORD recordCount, PBYTE buffer, DWORD bufferSize);
void ProcessMFTRecord(PBYTE pRecord, DWORD recordSize, LPWSTR volumeRoot);

// Worker thread function for processing MFT records
DWORD WINAPI ProcessMFTRecordsWorker(LPVOID lpParam);

// Pipe server
void StartPipeServer();
DWORD WINAPI PipeServerThread(LPVOID lpParam);
void HandlePipeClient(HANDLE hPipe);
BOOL SendResponse(HANDLE hPipe, LPCVOID pData, DWORD cbData);

// Service control
void SvcInstall();
void SvcUninstall();
void SvcStart();
void SvcStop();
void WINAPI SvcCtrlHandler(DWORD dwCtrl);
void WINAPI SvcMain(DWORD dwArgc, LPTSTR* lpszArgv);
void ReportSvcStatus(DWORD dwCurrentState, DWORD dwWin32ExitCode, DWORD dwWaitHint);
void SvcReportEvent(LPTSTR szFunction);
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam);

// Main entry point
int _tmain(int argc, TCHAR* argv[]);

#endif // FASTSEARCH_SERVICE_H
