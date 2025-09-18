#include "fastsearch_service.h"
#include <memory>
#include <mutex>

using namespace std;

// Get NTFS volume data
BOOL GetNtfsVolumeData(HANDLE hVolume, PNTFS_VOLUME_DATA_BUFFER pVolumeData) {
    if (!hVolume || hVolume == INVALID_HANDLE_VALUE || !pVolumeData) {
        return FALSE;
    }

    DWORD bytesReturned = 0;
    return DeviceIoControl(
        hVolume,                    // Handle to volume
        FSCTL_GET_NTFS_VOLUME_DATA, // Control code
        NULL,                       // No input buffer
        0,                          // Input buffer size
        pVolumeData,                // Output buffer
        sizeof(NTFS_VOLUME_DATA_BUFFER), // Output buffer size
        &bytesReturned,             // Bytes returned
        NULL                        // Overlapped
    ) != 0;
}


// Global critical section for thread safety
CRITICAL_SECTION gCS;

// Initialize the critical section in DllMain or WinMain
BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            InitializeCriticalSection(&gCS);
            break;
        case DLL_PROCESS_DETACH:
            DeleteCriticalSection(&gCS);
            break;
    }
    return TRUE;
}

// If this is not a DLL, you can initialize the critical section in main/WinMain
void InitializeGlobalCS() {
    static BOOL initialized = FALSE;
    if (!initialized) {
        InitializeCriticalSection(&gCS);
        initialized = TRUE;
    }
}

// Worker thread function for processing MFT records
DWORD WINAPI ProcessMFTRecordsWorker(LPVOID lpParam) {
    WORKER_THREAD_CTX* pCtx = (WORKER_THREAD_CTX*)lpParam;
    if (!pCtx) {
        return 1;
    }

    while (true) {
        // Wait for work
        DWORD waitResult = WaitForSingleObject(pCtx->hStartEvent, INFINITE);
        if (waitResult != WAIT_OBJECT_0) {
            break; // Error or shutdown
        }

        // Check if we should exit
        if (pCtx->shutdown) {
            break;
        }

        // Process the assigned MFT records
        for (DWORD i = 0; i < pCtx->recordCount; i++) {
            PBYTE pRecord = pCtx->pBuffer + (i * pCtx->recordSize);
            PMFT_RECORD_HEADER pHeader = (PMFT_RECORD_HEADER)pRecord;
            
            // Check for valid record signature ('FILE' in little-endian)
            if (pHeader->Signature == 0x454C4946) { // 'FILE'
                // Add to cache or process the record
                AddToCache(pCtx->startRecord + i, pRecord, pCtx->recordSize);
            }
        }

        // Signal completion
        SetEvent(pCtx->hCompleteEvent);
    }

    return 0;
}

// Service configuration
#define SVCNAME TEXT("FastSearchMCP")
#define SVC_DISPLAY_NAME TEXT("FastSearch MCP Service")
#define SVC_DESCRIPTION TEXT("Provides fast file search capabilities using MFT")
#define PIPE_NAME TEXT("\\\\.\\pipe\\FastSearchMCPService")
#define BUFSIZE 4096

// Global variables
MFTCacheEntry* gCacheHead = NULL;
MFTCacheEntry* gCacheTail = NULL;
DWORD gCacheSize = 0;
#define MAX_CACHE_ENTRIES 1000000  // 1 million entries in cache

// Service status and handles
SERVICE_STATUS gSvcStatus = { 0 };
SERVICE_STATUS_HANDLE gSvcStatusHandle = NULL;
HANDLE ghSvcStopEvent = NULL;
HANDLE ghPipe = INVALID_HANDLE_VALUE;
CacheManager gCache = { 0 };

// Critical sections for thread safety
CRITICAL_SECTION gCacheCS;
CRITICAL_SECTION gIndexCS;
CRITICAL_SECTION gAttrCacheCS;

// Global indices
FileNameIndex* gFileNameIndex = NULL;
AttributeCacheEntry* gAttrCache = NULL;
#define MAX_FILE_RECORDS 100000000     // 100 million max files
#define MAX_WORKER_THREADS 16          // Number of worker threads for parallel processing
#define MFT_READ_CHUNK_SIZE 1024       // Process 1024 records per chunk

// NTFS MFT related constants
#define MAX_PATH_LENGTH 32767
#define MAX_ATTR_SIZE 65536
#define CACHE_TTL_MS 300000  // 5 minutes

// Worker thread context is defined in the header file

// Process MFT record
VOID ProcessMFTRecord(PBYTE pRecord, DWORD recordSize, LPWSTR volumeRoot)
{
    if (!pRecord || recordSize < sizeof(MFT_RECORD_HEADER)) {
        return; // Invalid record
    }
    
    PMFT_RECORD_HEADER pHeader = (PMFT_RECORD_HEADER)pRecord;
    
    // Check if this is a valid MFT record
    if (pHeader->Signature != 0x454C4946) { // 'FILE' in little-endian
        return;
    }
    
    // Get the first attribute
    PBYTE pAttr = pRecord + pHeader->FirstAttributeOffset;
    PATTRIBUTE_RECORD_HEADER pAttrHeader = (PATTRIBUTE_RECORD_HEADER)pAttr;
    
    // Process attributes
    while ((PBYTE)pAttrHeader < pRecord + pHeader->UsedSize) {
        // Check for end of attributes
        if (pAttrHeader->TypeCode == 0xFFFFFFFF) {
            break;
        }
        
        // Process $FILE_NAME attribute
        if (pAttrHeader->TypeCode == ATTRIBUTE_FILE_NAME) {
            if (pAttrHeader->FormCode == 0) { // Resident
                PFILE_NAME pFileName = (PFILE_NAME)((PBYTE)pAttrHeader + pAttrHeader->Form.Resident.ValueOffset);
                
                // Add to file name index
                if (pFileName->FileNameLength > 0) {
                    WCHAR fileName[MAX_PATH] = {0};
                    size_t fileNameLength = static_cast<size_t>(pFileName->FileNameLength);
                    size_t maxCopy = MAX_PATH - 1;
                    size_t copyLength = (fileNameLength < maxCopy) ? fileNameLength : maxCopy;
                    wcsncpy_s(fileName, MAX_PATH, pFileName->FileName, copyLength);
                    fileName[copyLength] = L'\0';
                    
                    // Add to index (file name -> record number)
                    AddToFileIndex(pHeader->FileReferenceNumber, 
                                 pFileName->ParentDirectory, 
                                 fileName);
                }
            }
        }
        
        // Move to next attribute
        pAttr += pAttrHeader->RecordLength;
        pAttrHeader = (PATTRIBUTE_RECORD_HEADER)pAttr;
    }
}

// NTFS control codes
#define FSCTL_GET_NTFS_VOLUME_DATA CTL_CODE(FILE_DEVICE_FILE_SYSTEM, 25, METHOD_BUFFERED, FILE_ANY_ACCESS)
#define FSCTL_GET_NTFS_FILE_RECORD CTL_CODE(FILE_DEVICE_FILE_SYSTEM, 26, METHOD_BUFFERED, FILE_ANY_ACCESS)

// Use the NTFS_VOLUME_DATA_BUFFER from winioctl.h

// Global variables
// Function prototypes for NTFS operations
BOOL EnablePrivilege(LPCTSTR pszPrivilege);
HANDLE OpenVolume(LPCTSTR pszRootPath);
BOOL GetNtfsVolumeData(HANDLE hVolume, PNTFS_VOLUME_DATA_BUFFER pVolumeData);
DWORD GetMFTRecordSize(HANDLE hVolume);
BOOL ReadMFTRecords(HANDLE hVolume, ULONGLONG startRecord, DWORD recordCount, PBYTE buffer, DWORD bufferSize);
VOID ProcessMFTRecord(PBYTE pRecord, DWORD recordSize, LPWSTR volumeRoot);

// Function prototypes for pipe server
VOID StartPipeServer();
DWORD WINAPI PipeServerThread(LPVOID lpParam);
VOID HandlePipeClient(HANDLE hPipe);
BOOL SendResponse(HANDLE hPipe, LPCVOID pData, DWORD cbData);

// Forward declarations
VOID SvcInstall(void);
VOID WINAPI SvcCtrlHandler(DWORD);
VOID WINAPI SvcMain(DWORD, LPTSTR*);
VOID ReportSvcStatus(DWORD, DWORD, DWORD);
VOID SvcInit(DWORD, LPTSTR*);
VOID SvcReportEvent(LPTSTR);
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam);

// Cache initialization
VOID InitializeCaches() {
    // Initialize critical sections with spin count for better performance
    InitializeCriticalSectionAndSpinCount(&gCacheCS, 4000);
    InitializeCriticalSectionAndSpinCount(&gIndexCS, 4000);
    InitializeCriticalSectionAndSpinCount(&gAttrCacheCS, 4000);
    
    // Initialize cache with hash table
    gCache.capacity = MAX_CACHE_ENTRIES;
    gCache.size = 0;
    gCache.lruHead = gCache.lruTail = NULL;
    gCache.hashTable = (MFTCacheEntry**)calloc(MAX_CACHE_ENTRIES, sizeof(MFTCacheEntry*));
    
    // Create a dedicated heap for cache allocations
    gCache.hHeap = HeapCreate(0, 64 * 1024 * 1024, 0);  // 64MB initial size, growable
    
    gFileNameIndex = NULL;
    gAttrCache = NULL;
}

// Cleanup caches
VOID CleanupCaches() {
    // Clean MFT cache
    EnterCriticalSection(&gCacheCS);
    MFTCacheEntry* entry = gCacheHead;
    while (entry) {
        MFTCacheEntry* next = entry->next;
        free(entry->recordData);
        free(entry);
        entry = next;
    }
    gCacheHead = gCacheTail = NULL;
    gCacheSize = 0;
    LeaveCriticalSection(&gCacheCS);

    // Clean file name index
    EnterCriticalSection(&gIndexCS);
    FileNameIndex* index = gFileNameIndex;
    while (index) {
        FileNameIndex* next = index->next;
        free(index);
        index = next;
    }
    gFileNameIndex = NULL;
    LeaveCriticalSection(&gIndexCS);

    // Clean attribute cache
    EnterCriticalSection(&gAttrCacheCS);
    AttributeCacheEntry* attrEntry = gAttrCache;
    while (attrEntry) {
        AttributeCacheEntry* next = attrEntry->next;
        free(attrEntry->data);
        free(attrEntry);
        attrEntry = next;
    }
    gAttrCache = NULL;
    LeaveCriticalSection(&gAttrCacheCS);

    DeleteCriticalSection(&gCacheCS);
    DeleteCriticalSection(&gIndexCS);
    DeleteCriticalSection(&gAttrCacheCS);
}

// Add record to cache
VOID AddToCache(ULONGLONG recordNumber, PBYTE recordData, DWORD recordSize) {
    if (gCacheSize >= MAX_CACHE_ENTRIES) {
        // Remove least recently used entry
        EnterCriticalSection(&gCacheCS);
        if (gCacheTail) {
            MFTCacheEntry* toRemove = gCacheTail;
            if (toRemove->prev) {
                toRemove->prev->next = NULL;
                gCacheTail = toRemove->prev;
            } else {
                gCacheHead = gCacheTail = NULL;
            }
            free(toRemove->recordData);
            free(toRemove);
            gCacheSize--;
        }
        LeaveCriticalSection(&gCacheCS);
    }

    // Add new entry
    MFTCacheEntry* newEntry = (MFTCacheEntry*)malloc(sizeof(MFTCacheEntry));
    if (newEntry) {
        newEntry->recordNumber = recordNumber;
        newEntry->recordData = (PBYTE)malloc(recordSize);
        if (newEntry->recordData) {
            memcpy(newEntry->recordData, recordData, recordSize);
            newEntry->recordSize = recordSize;
            GetSystemTimeAsFileTime(&newEntry->lastAccessTime);
            newEntry->accessCount = 1;
            newEntry->next = gCacheHead;
            newEntry->prev = NULL;

            EnterCriticalSection(&gCacheCS);
            if (gCacheHead) {
                gCacheHead->prev = newEntry;
            } else {
                gCacheTail = newEntry;
            }
            gCacheHead = newEntry;
            gCacheSize++;
            LeaveCriticalSection(&gCacheCS);
        } else {
            free(newEntry);
        }
    }
}

// Get record from cache
PBYTE GetFromCache(ULONGLONG recordNumber, DWORD* pRecordSize) {
    EnterCriticalSection(&gCacheCS);
    MFTCacheEntry* entry = gCacheHead;
    while (entry) {
        if (entry->recordNumber == recordNumber) {
            // Move to front (MRU)
            if (entry != gCacheHead) {
                if (entry->prev) entry->prev->next = entry->next;
                if (entry->next) entry->next->prev = entry->prev;
                if (entry == gCacheTail) gCacheTail = entry->prev;
                entry->next = gCacheHead;
                entry->prev = NULL;
                if (gCacheHead) gCacheHead->prev = entry;
                gCacheHead = entry;
            }
            // Update access time and count
            GetSystemTimeAsFileTime(&entry->lastAccessTime);
            entry->accessCount++;
            *pRecordSize = entry->recordSize;
            PBYTE result = (PBYTE)malloc(entry->recordSize);
            if (result) {
                memcpy(result, entry->recordData, entry->recordSize);
            }
            LeaveCriticalSection(&gCacheCS);
            return result;
        }
        entry = entry->next;
    }
    LeaveCriticalSection(&gCacheCS);
    return NULL;
}

// Add file name to index
VOID AddToFileIndex(ULONGLONG recordNumber, ULONGLONG parentRecordNumber, LPCWSTR fileName) {
    FileNameIndex* newIndex = (FileNameIndex*)malloc(sizeof(FileNameIndex));
    if (newIndex) {
        wcsncpy_s(newIndex->fileName, MAX_PATH, fileName, _TRUNCATE);
        newIndex->recordNumber = recordNumber;
        newIndex->parentRecordNumber = parentRecordNumber;
        
        EnterCriticalSection(&gIndexCS);
        newIndex->next = gFileNameIndex;
        gFileNameIndex = newIndex;
        LeaveCriticalSection(&gIndexCS);
    }
}

// Find file in index
BOOL FindFileInIndex(LPCWSTR fileName, ULONGLONG* pRecordNumber) {
    EnterCriticalSection(&gIndexCS);
    FileNameIndex* index = gFileNameIndex;
    while (index) {
        if (_wcsicmp(index->fileName, fileName) == 0) {
            *pRecordNumber = index->recordNumber;
            LeaveCriticalSection(&gIndexCS);
            return TRUE;
        }
        index = index->next;
    }
    LeaveCriticalSection(&gIndexCS);
    return FALSE;
}

// Add attribute to cache
VOID AddToAttributeCache(ULONGLONG recordNumber, DWORD attrType, DWORD instance, PBYTE data, DWORD size) {
    if (!data || size == 0) {
        return;
    }
    
    EnterCriticalSection(&gAttrCacheCS);
    
    // Allocate new cache entry
    AttributeCacheEntry* newEntry = (AttributeCacheEntry*)malloc(sizeof(AttributeCacheEntry));
    if (newEntry) {
        newEntry->recordNumber = recordNumber;
        newEntry->attrType = attrType;
        newEntry->instance = instance;
        newEntry->data = (PBYTE)malloc(size);
        if (newEntry->data) {
            memcpy(newEntry->data, data, size);
            newEntry->size = size;
            GetSystemTimeAsFileTime(&newEntry->lastAccessTime);
            
            // Add to cache (simple implementation - in real code, handle LRU, etc.)
            newEntry->next = gAttrCache;
            gAttrCache = newEntry;
        } else {
            free(newEntry);
        }
    }
    
    LeaveCriticalSection(&gAttrCacheCS);
}

// Get attribute from cache
PBYTE GetFromAttributeCache(ULONGLONG recordNumber, DWORD attrType, DWORD instance, DWORD* pSize) {
    PBYTE result = NULL;
    
    EnterCriticalSection(&gAttrCacheCS);
    
    AttributeCacheEntry* entry = gAttrCache;
    AttributeCacheEntry* prev = NULL;
    
    while (entry) {
        if (entry->recordNumber == recordNumber && 
            entry->attrType == attrType && 
            entry->instance == instance) {
            
            // Found match - update last access time
            GetSystemTimeAsFileTime(&entry->lastAccessTime);
            
            // Move to front of list (simple LRU)
            if (prev) {
                prev->next = entry->next;
                entry->next = gAttrCache;
                gAttrCache = entry;
            }
            
            // Return the data
            if (pSize) {
                *pSize = entry->size;
            }
            result = entry->data;
            break;
        }
        
        prev = entry;
        entry = entry->next;
    }
    
    LeaveCriticalSection(&gAttrCacheCS);
    return result;
}

// Clean up old cache entries
VOID CleanupOldCacheEntries() {
    // Get current time
    FILETIME currentTime;
    GetSystemTimeAsFileTime(&currentTime);
    ULARGE_INTEGER current, entryTime;
    current.LowPart = currentTime.dwLowDateTime;
    current.HighPart = currentTime.dwHighDateTime;
    
    // 5 minutes in 100-nanosecond intervals
    const ULONGLONG FIVE_MINUTES = 5 * 60 * 1000 * 10000ULL;
    
    // Clean attribute cache
    EnterCriticalSection(&gAttrCacheCS);
    
    AttributeCacheEntry* prevAttr = NULL;
    AttributeCacheEntry* attrEntry = gAttrCache;
    
    while (attrEntry) {
        entryTime.LowPart = attrEntry->lastAccessTime.dwLowDateTime;
        entryTime.HighPart = attrEntry->lastAccessTime.dwHighDateTime;
        
        if ((current.QuadPart - entryTime.QuadPart) > FIVE_MINUTES) {
            // Remove entry from list
            if (prevAttr) {
                prevAttr->next = attrEntry->next;
            } else {
                gAttrCache = attrEntry->next;
            }
            
            // Free memory
            AttributeCacheEntry* toDelete = attrEntry;
            attrEntry = attrEntry->next;
            
            if (toDelete->data) {
                free(toDelete->data);
            }
            free(toDelete);
        } else {
            prevAttr = attrEntry;
            attrEntry = attrEntry->next;
        }
    }
    
    LeaveCriticalSection(&gAttrCacheCS);

    // Clean MFT cache
    EnterCriticalSection(&gCacheCS);
    
    MFTCacheEntry* prevMft = NULL;
    MFTCacheEntry* mftEntry = gCacheHead;
    
    while (mftEntry) {
        entryTime.LowPart = mftEntry->lastAccessTime.dwLowDateTime;
        entryTime.HighPart = mftEntry->lastAccessTime.dwHighDateTime;
        
        if ((current.QuadPart - entryTime.QuadPart) > FIVE_MINUTES) {
            // Remove from cache
            if (prevMft) {
                prevMft->next = mftEntry->next;
            } else {
                gCacheHead = mftEntry->next;
            }
            
            if (mftEntry == gCacheTail) {
                gCacheTail = prevMft;
            }
            
            // Free memory
            MFTCacheEntry* toDelete = mftEntry;
            mftEntry = mftEntry->next;
            
            if (toDelete->recordData) {
                free(toDelete->recordData);
            }
            free(toDelete);
        } else {
            prevMft = mftEntry;
            mftEntry = mftEntry->next;
        }
    }
    
    // Update cache size
    gCacheSize = 0;
    for (MFTCacheEntry* e = gCacheHead; e != NULL; e = e->next) {
        gCacheSize++;
    }
    
    LeaveCriticalSection(&gCacheCS);
}

// Main entry point
int _tmain(int argc, TCHAR* argv[]) {
    // Initialize critical sections
    InitializeCriticalSection(&gCS);
    InitializeCriticalSection(&gIndexCS);
    InitializeCriticalSection(&gAttrCacheCS);
    
    // Handle command line arguments
    if (argc > 1) {
        if (_tcscmp(argv[1], TEXT("--install")) == 0) {
            printf("Installing FastSearch MCP Service...\n");
            SvcInstall();
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 0;
        }
        else if (_tcscmp(argv[1], TEXT("--uninstall")) == 0) {
            printf("Uninstalling FastSearch MCP Service...\n");
            SvcUninstall();
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 0;
        }
        else if (_tcscmp(argv[1], TEXT("--start")) == 0) {
            printf("Starting FastSearch MCP Service...\n");
            SvcStart();
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 0;
        }
        else if (_tcscmp(argv[1], TEXT("--stop")) == 0) {
            printf("Stopping FastSearch MCP Service...\n");
            SvcStop();
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 0;
        }
        else if (_tcscmp(argv[1], TEXT("--help")) == 0 || _tcscmp(argv[1], TEXT("-h")) == 0) {
            printf("FastSearch MCP Service\n");
            printf("Usage: %s [command]\n", argv[0]);
            printf("Commands:\n");
            printf("  --install    Install the service (requires UAC)\n");
            printf("  --uninstall  Uninstall the service (requires UAC)\n");
            printf("  --start      Start the service\n");
            printf("  --stop       Stop the service\n");
            printf("  --help       Show this help\n");
            printf("  (no args)    Run as service\n");
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 0;
        }
        else {
            printf("Unknown command: %s\n", argv[1]);
            printf("Use --help for usage information\n");
            DeleteCriticalSection(&gAttrCacheCS);
            DeleteCriticalSection(&gIndexCS);
            DeleteCriticalSection(&gCS);
            return 1;
        }
    }
    
    // Initialize service
    SERVICE_TABLE_ENTRY DispatchTable[] = {
        { (LPWSTR)SVCNAME, (LPSERVICE_MAIN_FUNCTION)SvcMain },
        { NULL, NULL }
    };
    
    // Start the service control dispatcher
    if (!StartServiceCtrlDispatcher(DispatchTable)) {
        SvcReportEvent((LPWSTR)L"StartServiceCtrlDispatcher");
    }
    
    // Clean up
    DeleteCriticalSection(&gAttrCacheCS);
    DeleteCriticalSection(&gIndexCS);
    DeleteCriticalSection(&gCS);
    
    return 0;
}

// Install the service
VOID SvcInstall() {
    SC_HANDLE schSCManager;
    SC_HANDLE schService;
    TCHAR szPath[MAX_PATH];

    if (!GetModuleFileName(NULL, szPath, MAX_PATH)) {
        printf("Cannot install service (%d)\n", GetLastError());
        return;
    }

    // Get a handle to the SCM database
    schSCManager = OpenSCManager(
        NULL,                    // local computer
        NULL,                    // ServicesActive database
        SC_MANAGER_ALL_ACCESS);  // full access rights

    if (NULL == schSCManager) {
        printf("OpenSCManager failed (%d)\n", GetLastError());
        return;
    }

    // Create the service
    schService = CreateService(
        schSCManager,              // SCM database
        SVCNAME,                   // name of service
        SVC_DISPLAY_NAME,          // service name to display
        SERVICE_ALL_ACCESS,        // desired access
        SERVICE_WIN32_OWN_PROCESS, // service type
        SERVICE_AUTO_START,        // start type
        SERVICE_ERROR_NORMAL,      // error control type
        szPath,                    // path to service's binary
        NULL,                      // no load ordering group
        NULL,                      // no tag identifier
        NULL,                      // no dependencies
        NULL,                      // LocalSystem account
        NULL);                     // no password

    if (schService == NULL) {
        printf("CreateService failed (%d)\n", GetLastError());
        CloseServiceHandle(schSCManager);
        return;
    }
    else {
        printf("Service installed successfully\n");
    }

    // Set the service description
    SERVICE_DESCRIPTION sd;
    sd.lpDescription = (LPWSTR)SVC_DESCRIPTION;
    ChangeServiceConfig2(schService, SERVICE_CONFIG_DESCRIPTION, &sd);

    CloseServiceHandle(schService);
    CloseServiceHandle(schSCManager);
}

// Uninstall the service
VOID SvcUninstall() {
    SC_HANDLE schSCManager;
    SC_HANDLE schService;

    // Get a handle to the SCM database
    schSCManager = OpenSCManager(
        NULL,                    // local computer
        NULL,                    // ServicesActive database
        SC_MANAGER_ALL_ACCESS);  // full access rights

    if (NULL == schSCManager) {
        printf("OpenSCManager failed (%d)\n", GetLastError());
        return;
    }

    // Open the service
    schService = OpenService(
        schSCManager,            // SCM database
        SVCNAME,                 // name of service
        DELETE);                 // need DELETE access

    if (schService == NULL) {
        printf("OpenService failed (%d)\n", GetLastError());
        CloseServiceHandle(schSCManager);
        return;
    }

    // Delete the service
    if (DeleteService(schService)) {
        printf("Service uninstalled successfully\n");
    }
    else {
        printf("DeleteService failed (%d)\n", GetLastError());
    }

    CloseServiceHandle(schService);
    CloseServiceHandle(schSCManager);
}

// Start the service
VOID SvcStart() {
    SC_HANDLE schSCManager;
    SC_HANDLE schService;

    // Get a handle to the SCM database
    schSCManager = OpenSCManager(
        NULL,                    // local computer
        NULL,                    // ServicesActive database
        SC_MANAGER_ALL_ACCESS);  // full access rights

    if (NULL == schSCManager) {
        printf("OpenSCManager failed (%d)\n", GetLastError());
        return;
    }

    // Open the service
    schService = OpenService(
        schSCManager,            // SCM database
        SVCNAME,                 // name of service
        SERVICE_START);          // need START access

    if (schService == NULL) {
        printf("OpenService failed (%d)\n", GetLastError());
        CloseServiceHandle(schSCManager);
        return;
    }

    // Start the service
    if (StartService(schService, 0, NULL)) {
        printf("Service started successfully\n");
    }
    else {
        printf("StartService failed (%d)\n", GetLastError());
    }

    CloseServiceHandle(schService);
    CloseServiceHandle(schSCManager);
}

// Stop the service
VOID SvcStop() {
    SC_HANDLE schSCManager;
    SC_HANDLE schService;
    SERVICE_STATUS_PROCESS ssp;

    // Get a handle to the SCM database
    schSCManager = OpenSCManager(
        NULL,                    // local computer
        NULL,                    // ServicesActive database
        SC_MANAGER_ALL_ACCESS);  // full access rights

    if (NULL == schSCManager) {
        printf("OpenSCManager failed (%d)\n", GetLastError());
        return;
    }

    // Open the service
    schService = OpenService(
        schSCManager,            // SCM database
        SVCNAME,                 // name of service
        SERVICE_STOP | SERVICE_QUERY_STATUS); // need STOP and QUERY access

    if (schService == NULL) {
        printf("OpenService failed (%d)\n", GetLastError());
        CloseServiceHandle(schSCManager);
        return;
    }

    // Send a stop control request to the service
    if (ControlService(schService, SERVICE_CONTROL_STOP, (LPSERVICE_STATUS)&ssp)) {
        printf("Service stop request sent\n");
        
        // Wait for the service to stop
        DWORD dwStartTime = GetTickCount();
        DWORD dwTimeout = 30000; // 30-second time-out

        while (ssp.dwCurrentState != SERVICE_STOPPED) {
            Sleep(ssp.dwWaitHint);
            if (ssp.dwCurrentState == SERVICE_STOPPED)
                break;
            if ((GetTickCount() - dwStartTime) > dwTimeout) {
                printf("Service stop timed out\n");
                break;
            }
            if (!QueryServiceStatusEx(schService, SC_STATUS_PROCESS_INFO, (LPBYTE)&ssp, sizeof(SERVICE_STATUS_PROCESS), NULL)) {
                printf("QueryServiceStatusEx failed (%d)\n", GetLastError());
                break;
            }
        }
        
        if (ssp.dwCurrentState == SERVICE_STOPPED) {
            printf("Service stopped successfully\n");
        }
    }
    else {
        printf("ControlService failed (%d)\n", GetLastError());
    }

    CloseServiceHandle(schService);
    CloseServiceHandle(schSCManager);
}

// Entry point for the service
VOID WINAPI SvcMain(DWORD dwArgc, LPTSTR* lpszArgv) {
    // Register the handler function for the service
    gSvcStatusHandle = RegisterServiceCtrlHandler(SVCNAME, SvcCtrlHandler);
    
    if (!gSvcStatusHandle) {
        SvcReportEvent((LPTSTR)TEXT("RegisterServiceCtrlHandler"));
        return;
    }
    
    // These SERVICE_STATUS members remain as set here
    gSvcStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    gSvcStatus.dwServiceSpecificExitCode = 0;
    
    // Report initial status to the SCM
    ReportSvcStatus(SERVICE_START_PENDING, NO_ERROR, 3000);
    
    // Initialize global critical section
    InitializeCriticalSectionAndSpinCount(&gCS, 4000);
    
    // Enable required privileges
    EnablePrivilege(SE_BACKUP_NAME);
    EnablePrivilege(SE_MANAGE_VOLUME_NAME);
    EnablePrivilege(SE_RESTORE_NAME);
    EnablePrivilege(SE_MANAGE_VOLUME_NAME);
    
    // Report that the service is starting
    ReportSvcStatus(SERVICE_START_PENDING, NO_ERROR, 3000);
    
    // Create the service stop event first
    ghSvcStopEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (ghSvcStopEvent == NULL) {
        ReportSvcStatus(SERVICE_STOPPED, GetLastError(), 0);
        return;
    }
    
    // Start the named pipe server
    StartPipeServer();
    
    // Start the named pipe server thread
    HANDLE hPipeThread = CreateThread(
        NULL,              // Default security
        0,                 // Default stack size
        PipeServerThread,   // Thread function
        NULL,              // Thread parameter
        0,                 // Start immediately
        NULL               // Thread ID
    );
    
    if (hPipeThread == NULL) {
        SvcReportEvent((LPTSTR)TEXT("CreateThread(PipeServerThread)"));
        ReportSvcStatus(SERVICE_STOPPED, GetLastError(), 0);
        return;
    }
    
    // Report that the service is starting
    ReportSvcStatus(SERVICE_START_PENDING, NO_ERROR, 3000);
    
    // Initialize volume handles and MFT processing with memory-mapped I/O
    HANDLE hVolume = CreateFile(TEXT("\\\\.\\C:$"), 
                              GENERIC_READ | GENERIC_WRITE, 
                              FILE_SHARE_READ | FILE_SHARE_WRITE,
                              NULL,
                              OPEN_EXISTING,
                              FILE_FLAG_NO_BUFFERING | FILE_FLAG_RANDOM_ACCESS,
                              NULL);
    
    if (hVolume != INVALID_HANDLE_VALUE) {
        // Get MFT size and record size
        NTFS_VOLUME_DATA_BUFFER volumeData = {0};
        DWORD bytesReturned = 0;
        DWORD recordSize = 0;
        LARGE_INTEGER mftSize = {0};
        
        // Get volume data using FSCTL_GET_NTFS_VOLUME_DATA
        if (!GetNtfsVolumeData(hVolume, &volumeData)) {
            DWORD error = GetLastError();
            CloseHandle(hVolume);
            return;
        }
        
        recordSize = volumeData.BytesPerFileRecordSegment;
        mftSize.QuadPart = volumeData.MftValidDataLength.QuadPart;
        
        HANDLE hMftMapping = CreateFileMapping(hVolume, 
                                             NULL, 
                                             PAGE_READONLY, 
                                             mftSize.HighPart, 
                                             mftSize.LowPart, 
                                             NULL);
        
        if (hMftMapping != NULL) {
            PBYTE pMftBase = (PBYTE)MapViewOfFile(hMftMapping, FILE_MAP_READ, 0, 0, 0);
            
            if (pMftBase) {
                // Create worker threads
                WORKER_THREAD_CTX workers[MAX_WORKER_THREADS] = {0};
                DWORD activeWorkers = 0;
                
                // Initialize worker threads
                for (DWORD i = 0; i < MAX_WORKER_THREADS; i++) {
                    workers[i].hStartEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
                    workers[i].hCompleteEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
                    workers[i].hThread = CreateThread(NULL, 0, ProcessMFTRecordsWorker, 
                                                   &workers[i], 0, &workers[i].threadId);
                    activeWorkers++;
                }
                
                // Using MFT_READ_CHUNK_SIZE from header file
                ULONGLONG totalRecords = mftSize.QuadPart / recordSize;
                ULONGLONG recordsProcessed = 0;
                        
                while (recordsProcessed < totalRecords) {
                    // Check for service stop
                    if (WaitForSingleObject(ghSvcStopEvent, 0) == WAIT_OBJECT_0) {
                        break;
                    }
                    
                    // Find available worker
                    DWORD workerIdx = 0;
                    while (workerIdx < activeWorkers) {
                        if (WaitForSingleObject(workers[workerIdx].hCompleteEvent, 0) == WAIT_OBJECT_0) {
                            // Worker is available, assign work
                            DWORD remainingRecords = (DWORD)(totalRecords - recordsProcessed);
                            DWORD chunkSize = (MFT_READ_CHUNK_SIZE < remainingRecords) ? MFT_READ_CHUNK_SIZE : remainingRecords;
                            
                            workers[workerIdx].pBuffer = pMftBase + (recordsProcessed * recordSize);
                            workers[workerIdx].recordCount = chunkSize;
                            workers[workerIdx].startRecord = recordsProcessed;
                            workers[workerIdx].recordSize = recordSize;
                            
                            ResetEvent(workers[workerIdx].hCompleteEvent);
                            SetEvent(workers[workerIdx].hStartEvent);
                            
                            recordsProcessed += chunkSize;
                            break;
                        }
                        workerIdx++;
                    }

                    // If no workers available, wait a bit
                    if (workerIdx >= activeWorkers) {
                        Sleep(1);
                    }

                    // Periodically clean up old cache entries
                    if (recordsProcessed % 10000 == 0) {
                        CleanupOldCacheEntries();
                    }
                }

                // Signal all workers to exit
                for (DWORD i = 0; i < activeWorkers; i++) {
                    workers[i].pBuffer = NULL;
                    workers[i].recordCount = 0;
                    SetEvent(workers[i].hStartEvent);
                }

                // Wait for all workers to finish
                WaitForMultipleObjects(activeWorkers, 
                                      &workers[0].hCompleteEvent, 
                                      TRUE, 
                                      INFINITE);

                // Clean up workers
                for (DWORD i = 0; i < activeWorkers; i++) {
                    if (workers[i].hThread) {
                        TerminateThread(workers[i].hThread, 0);
                        CloseHandle(workers[i].hThread);
                    }
                    if (workers[i].hStartEvent) {
                        CloseHandle(workers[i].hStartEvent);
                    }
                    if (workers[i].hCompleteEvent) {
                        CloseHandle(workers[i].hCompleteEvent);
                    }
                }
                
                UnmapViewOfFile(pMftBase);
            }
            CloseHandle(hMftMapping);
        }
    }
    CloseHandle(hVolume);
    
    // Report that the service is now running
    ReportSvcStatus(SERVICE_RUNNING, NO_ERROR, 0);
    
    // Start the service worker thread
    HANDLE hWorkerThread = CreateThread(
        NULL,              // Default security
        0,                 // Default stack size
        ServiceWorkerThread, // Thread function
        NULL,              // Thread parameter
        0,                 // Start immediately
        NULL               // Thread ID
    );
    
    if (hWorkerThread == NULL) {
        ReportSvcStatus(SERVICE_STOPPED, GetLastError(), 0);
        return;
    }
    
    // Wait for the service stop event
    WaitForSingleObject(ghSvcStopEvent, INFINITE);
    
    // Clean up
    CloseHandle(ghSvcStopEvent);
    CloseHandle(hWorkerThread);
    CloseHandle(hPipeThread);
    
    // Report that the service is stopping
    ReportSvcStatus(SERVICE_STOPPED, NO_ERROR, 0);
}

// Service worker thread
DWORD WINAPI ServiceWorkerThread(LPVOID lpParam) {
    // Main service loop
    while (true) {
        // Check if the service is stopping
        if (WaitForSingleObject(ghSvcStopEvent, 1000) == WAIT_OBJECT_0) {
            break;
        }
        
        // Service-specific periodic tasks
        static DWORD lastCleanup = 0;
        DWORD currentTime = GetTickCount();
        if (currentTime - lastCleanup > 300000) { // Every 5 minutes
            CleanupOldCacheEntries();
            lastCleanup = currentTime;
        }
    }
    
    return 0;
}

// Global variables are already defined at the top of the file
// No need to redefine them here

// Enable a specific privilege for the current process
BOOL EnablePrivilege(LPCTSTR pszPrivilege) {
    HANDLE hToken = NULL;
    TOKEN_PRIVILEGES tp = {0};
    LUID luid = {0};
    
    if (!pszPrivilege) {
        return FALSE;
    }

    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) {
        return FALSE;
    }

    if (!LookupPrivilegeValue(NULL, pszPrivilege, &luid)) {
        CloseHandle(hToken);
        return FALSE;
    }

    tp.PrivilegeCount = 1;
    tp.Privileges[0].Luid = luid;
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;

    if (!AdjustTokenPrivileges(hToken, FALSE, &tp, sizeof(TOKEN_PRIVILEGES), (PTOKEN_PRIVILEGES)NULL, (PDWORD)NULL)) {
        CloseHandle(hToken);
        return FALSE;
    }

    CloseHandle(hToken);
    return TRUE;
}

// Get MFT record size
DWORD GetMFTRecordSize(HANDLE hVolume) {
    NTFS_VOLUME_DATA_BUFFER volumeData;
    if (GetNtfsVolumeData(hVolume, &volumeData)) {
        return volumeData.BytesPerFileRecordSegment;
    }
    return 1024; // Default size if we can't determine it
}

// Read MFT records
BOOL ReadMFTRecords(HANDLE hVolume, ULONGLONG startRecord, DWORD recordCount, PBYTE buffer, DWORD bufferSize) {
    STARTING_VCN_INPUT_BUFFER inputBuffer;
    inputBuffer.StartingVcn.QuadPart = startRecord;
    
    return DeviceIoControl(
        hVolume,
        FSCTL_GET_NTFS_FILE_RECORD,
        &inputBuffer,
        sizeof(inputBuffer),
        buffer,
        bufferSize,
        NULL,
        NULL
    );
}

// Start the named pipe server
VOID StartPipeServer() {
    // Create the named pipe
    SECURITY_ATTRIBUTES sa;
    SECURITY_DESCRIPTOR sd;
    
    // Initialize security descriptor
    InitializeSecurityDescriptor(&sd, SECURITY_DESCRIPTOR_REVISION);
    SetSecurityDescriptorDacl(&sd, TRUE, NULL, FALSE);
    
    // Set up security attributes
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.lpSecurityDescriptor = &sd;
    sa.bInheritHandle = FALSE;
    
    // Create the named pipe
    ghPipe = CreateNamedPipe(
        PIPE_NAME,                  // Pipe name
        PIPE_ACCESS_DUPLEX,         // Read/write access
        PIPE_TYPE_MESSAGE |         // Message type pipe
        PIPE_READMODE_MESSAGE |     // Message-read mode
        PIPE_WAIT,                  // Blocking mode
        PIPE_UNLIMITED_INSTANCES,   // Max instances
        BUFSIZE,                    // Output buffer size
        BUFSIZE,                    // Input buffer size
        0,                          // Default timeout
        &sa                         // Security attributes
    );
    
    if (ghPipe == INVALID_HANDLE_VALUE) {
        SvcReportEvent((LPTSTR)TEXT("CreateNamedPipe"));
        return;
    }
    
    // Start a thread to handle pipe connections
    HANDLE hThread = CreateThread(
        NULL,              // Default security
        0,                 // Default stack size
        PipeServerThread,  // Thread function
        NULL,              // Thread parameter
        0,                 // Start immediately
        NULL               // Thread ID
    );
    
    if (hThread == NULL) {
        SvcReportEvent((LPTSTR)TEXT("CreateThread(PipeServerThread)"));
        CloseHandle(ghPipe);
        ghPipe = INVALID_HANDLE_VALUE;
    } else {
        CloseHandle(hThread);
    }
}

// Pipe server thread
DWORD WINAPI PipeServerThread(LPVOID lpParam) {
    BOOL fConnected;
    HANDLE hPipe = INVALID_HANDLE_VALUE;
    
    while (1) {
        // Check if service is stopping
        if (WaitForSingleObject(ghSvcStopEvent, 0) == WAIT_OBJECT_0) {
            break;
        }
        
        // Wait for a client to connect
        fConnected = ConnectNamedPipe(ghPipe, NULL) ? TRUE : (GetLastError() == ERROR_PIPE_CONNECTED);
        
        if (fConnected) {
            HandlePipeClient(ghPipe);
        }
        
        // Disconnect the pipe instance
        DisconnectNamedPipe(ghPipe);
    }
    
    return 0;
}

// Handle client connection
VOID HandlePipeClient(HANDLE hPipe) {
    BYTE request[BUFSIZE];
    DWORD cbBytesRead, cbReplyBytes, cbWritten;
    BOOL fSuccess;
    
    // Read client requests
    fSuccess = ReadFile(
        hPipe,              // Handle to pipe
        request,            // Buffer to receive data
        BUFSIZE * sizeof(TCHAR), // Size of buffer
        &cbBytesRead,       // Number of bytes read
        NULL                // Not overlapped I/O
    );
    
    if (!fSuccess || cbBytesRead == 0) {
        return;
    }
    
    // Process the request and prepare a response
    // This is a simplified example - in a real application, you would parse the request
    // and perform the appropriate action (e.g., search, query MFT, etc.)
    
    const char* response = "Service request processed";
    
    // Write the response back to the client
    fSuccess = WriteFile(
        hPipe,                      // Handle to pipe
        response,                   // Buffer to write
        (DWORD)strlen(response) + 1, // Bytes to write (including null)
        &cbWritten,                 // Bytes written
        NULL                        // Not overlapped I/O
    );
    
    if (!fSuccess) {
        SvcReportEvent((LPTSTR)TEXT("WriteFile to pipe failed"));
    }
}

// Send a response through the pipe
BOOL SendResponse(HANDLE hPipe, LPCVOID pData, DWORD cbData) {
    DWORD cbWritten;
    return WriteFile(hPipe, pData, cbData, &cbWritten, NULL);
}

// Service control handler
VOID WINAPI SvcCtrlHandler(DWORD dwCtrl) {
    switch (dwCtrl) {
    case SERVICE_CONTROL_STOP:
        ReportSvcStatus(SERVICE_STOP_PENDING, NO_ERROR, 0);
        SetEvent(ghSvcStopEvent);
        ReportSvcStatus(gSvcStatus.dwCurrentState, NO_ERROR, 0);
        break;
    case SERVICE_CONTROL_INTERROGATE:
        break;
    default:
        break;
    }
}

// Helper function to report service status
VOID ReportSvcStatus(DWORD dwCurrentState, DWORD dwWin32ExitCode, DWORD dwWaitHint) {
    static DWORD dwCheckPoint = 1;

    gSvcStatus.dwCurrentState = dwCurrentState;
    gSvcStatus.dwWin32ExitCode = dwWin32ExitCode;
    gSvcStatus.dwWaitHint = dwWaitHint;

    if (dwCurrentState == SERVICE_START_PENDING)
        gSvcStatus.dwControlsAccepted = 0;
    else
        gSvcStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP;

    if ((dwCurrentState == SERVICE_RUNNING) || (dwCurrentState == SERVICE_STOPPED))
        gSvcStatus.dwCheckPoint = 0;
    else
        gSvcStatus.dwCheckPoint = dwCheckPoint++;

    SetServiceStatus(gSvcStatusHandle, &gSvcStatus);
}

// Write a message to the event log
VOID SvcReportEvent(LPTSTR szFunction) {
    HANDLE hEventSource;
    LPCTSTR lpszStrings[2];
    TCHAR Buffer[80];

    hEventSource = RegisterEventSource(NULL, SVCNAME);

    if (hEventSource) {
        StringCchPrintf(Buffer, 80, TEXT("%s failed with %d"), szFunction, GetLastError());

        lpszStrings[0] = SVCNAME;
        lpszStrings[1] = Buffer;

        ReportEvent(hEventSource,        // event log handle
            EVENTLOG_ERROR_TYPE,         // event type
            0,                          // event category
            0,                          // event identifier
            NULL,                       // no security identifier
            2,                          // size of lpszStrings array
            0,                          // no binary data
            lpszStrings,                // array of strings
            NULL);                      // no binary data

        DeregisterEventSource(hEventSource);
    }
}
