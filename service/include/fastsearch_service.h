#pragma once

#include <windows.h>
#include <winioctl.h>
#include <algorithm>

// Forward declarations
typedef struct _MFT_RECORD_HEADER MFT_RECORD_HEADER, *PMFT_RECORD_HEADER;
typedef struct _ATTRIBUTE_RECORD_HEADER ATTRIBUTE_RECORD_HEADER, *PATTRIBUTE_RECORD_HEADER;
typedef struct _FILE_NAME FILE_NAME, *PFILE_NAME;

typedef enum _NTFS_ATTR_TYPE {
    ATTR_STANDARD_INFORMATION = 0x10,
    ATTR_ATTRIBUTE_LIST = 0x20,
    ATTR_FILE_NAME = 0x30,
    ATTR_OBJECT_ID = 0x40,
    ATTR_SECURITY_DESCRIPTOR = 0x50,
    ATTR_VOLUME_NAME = 0x60,
    ATTR_VOLUME_INFORMATION = 0x70,
    ATTR_DATA = 0x80,
    ATTR_INDEX_ROOT = 0x90,
    ATTR_INDEX_ALLOCATION = 0xA0,
    ATTR_BITMAP = 0xB0
} NTFS_ATTR_TYPE;

// NTFS Volume Data Buffer
typedef struct {
    LARGE_INTEGER VolumeSerialNumber;
    LARGE_INTEGER NumberSectors;
    LARGE_INTEGER TotalClusters;
    LARGE_INTEGER FreeClusters;
    LARGE_INTEGER TotalReserved;
    DWORD BytesPerSector;
    DWORD BytesPerCluster;
    DWORD BytesPerFileRecordSegment;
    DWORD ClustersPerFileRecordSegment;
    LARGE_INTEGER MftValidDataLength;
    LARGE_INTEGER MftStartLcn;
    LARGE_INTEGER Mft2StartLcn;
    LARGE_INTEGER MftZoneStart;
    LARGE_INTEGER MftZoneEnd;
} NTFS_VOLUME_DATA_BUFFER, *PNTFS_VOLUME_DATA_BUFFER;

// Cache manager structure
typedef struct {
    // Cache management functions will be implemented in the source file
} CacheManager;

// File name index entry
typedef struct _FileNameIndex {
    WCHAR fileName[MAX_PATH];
    ULONGLONG parentRecordNumber;
    ULONGLONG recordNumber;
    struct _FileNameIndex* next;
} FileNameIndex;

// Attribute cache entry
typedef struct _AttributeCacheEntry {
    ULONGLONG recordNumber;
    NTFS_ATTR_TYPE attrType;
    DWORD instance;
    PBYTE data;
    DWORD size;
    struct _AttributeCacheEntry* next;
} AttributeCacheEntry;

// Worker thread context
typedef struct {
    HANDLE hThread;
    DWORD threadId;
    HANDLE hStartEvent;
    HANDLE hCompleteEvent;
    PBYTE pBuffer;
    DWORD recordCount;
    ULONGLONG startRecord;
    DWORD recordSize;
} WORKER_THREAD_CTX;

// Function declarations
VOID ProcessMFTRecord(PBYTE pRecord, DWORD recordSize, LPWSTR volumeRoot);
BOOL EnablePrivilege(LPCTSTR pszPrivilege);
HANDLE OpenVolume(LPCTSTR pszRootPath);
BOOL GetNtfsVolumeData(HANDLE hVolume, PNTFS_VOLUME_DATA_BUFFER pVolumeData);
DWORD GetMFTRecordSize(HANDLE hVolume);
BOOL ReadMFTRecords(HANDLE hVolume, ULONGLONG startRecord, DWORD recordCount, PBYTE buffer, DWORD bufferSize);
VOID StartPipeServer();
DWORD WINAPI PipeServerThread(LPVOID lpParam);
VOID HandlePipeClient(HANDLE hPipe);
BOOL SendResponse(HANDLE hPipe, LPCVOID pData, DWORD cbData);
VOID SvcInstall();
VOID SvcUninstall();
VOID SvcCtrlHandler(DWORD);
VOID SvcMain(DWORD, LPTSTR*);
VOID ReportSvcStatus(DWORD, DWORD, DWORD);
VOID SvcInit(DWORD, LPTSTR*);
VOID SvcReportEvent(LPTSTR);
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam);

// Cache management functions
VOID InitializeCaches();
VOID CleanupCaches();
VOID AddToCache(ULONGLONG recordNumber, PBYTE recordData, DWORD recordSize);
PBYTE GetFromCache(ULONGLONG recordNumber, DWORD* pRecordSize);
VOID AddToFileIndex(ULONGLONG recordNumber, ULONGLONG parentRecordNumber, LPCWSTR fileName);
BOOL FindFileInIndex(LPCWSTR fileName, ULONGLONG* pRecordNumber);
VOID AddToAttributeCache(ULONGLONG recordNumber, NTFS_ATTR_TYPE attrType, DWORD instance, PBYTE data, DWORD size);
PBYTE GetFromAttributeCache(ULONGLONG recordNumber, NTFS_ATTR_TYPE attrType, DWORD instance, DWORD* pSize);
VOID CleanupOldCacheEntries();
