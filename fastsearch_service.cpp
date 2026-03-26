#include "fastsearch_service.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

// Windows security includes
#include <aclapi.h>
#include <sddl.h>

// JSON parsing (simple implementation)
#include <regex>

namespace {

struct ServiceContext {
    SERVICE_STATUS status{};
    SERVICE_STATUS_HANDLE statusHandle = nullptr;
    HANDLE stopEvent = nullptr;
    HANDLE* workerThreads = nullptr;
    DWORD workerThreadCount = 0;
    HANDLE eventSource = nullptr;
    bool running = false;
};

ServiceContext g_ctx;

void ReportServiceStatus(DWORD currentState, DWORD win32ExitCode = NO_ERROR, DWORD waitHint = 0) {
    if (!g_ctx.statusHandle) {
        return;
    }

    try {
        g_ctx.status.dwCurrentState = currentState;
        g_ctx.status.dwWin32ExitCode = win32ExitCode;
        g_ctx.status.dwWaitHint = waitHint;

        if (currentState == SERVICE_START_PENDING) {
            g_ctx.status.dwControlsAccepted = 0;
        } else {
            g_ctx.status.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
        }

        if (!SetServiceStatus(g_ctx.statusHandle, &g_ctx.status)) {
            const DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"SetServiceStatus failed for state " << currentState << L" with error " << error;
            LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
        }
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in ReportServiceStatus: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in ReportServiceStatus");
    }
}

DWORD WINAPI ServiceWorkerThread(LPVOID threadId) {
    const DWORD_PTR id_ptr = reinterpret_cast<DWORD_PTR>(threadId);
    const DWORD id = static_cast<DWORD>(id_ptr);
    try {
        std::wstringstream ss;
        ss << L"Service worker thread " << id << L" started";
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss.str());

        while (g_ctx.running) {
            // Create security descriptor that allows all users to connect
            SECURITY_ATTRIBUTES sa = {};
            SECURITY_DESCRIPTOR sd = {};
            HANDLE pipe = INVALID_HANDLE_VALUE;
            
            // Initialize security descriptor
            if (InitializeSecurityDescriptor(&sd, SECURITY_DESCRIPTOR_REVISION)) {
                // Create a DACL that allows Everyone to connect
                SID_IDENTIFIER_AUTHORITY worldAuth = SECURITY_WORLD_SID_AUTHORITY;
                PSID everyoneSid = nullptr;
                
                if (AllocateAndInitializeSid(&worldAuth, 1, SECURITY_WORLD_RID, 0, 0, 0, 0, 0, 0, 0, &everyoneSid)) {
                    EXPLICIT_ACCESS_W ea = {};
                    ea.grfAccessPermissions = FILE_GENERIC_READ | FILE_GENERIC_WRITE | SYNCHRONIZE;
                    ea.grfAccessMode = SET_ACCESS;
                    ea.grfInheritance = NO_INHERITANCE;
                    ea.Trustee.TrusteeForm = TRUSTEE_IS_SID;
                    ea.Trustee.TrusteeType = TRUSTEE_IS_WELL_KNOWN_GROUP;
                    ea.Trustee.ptstrName = reinterpret_cast<LPWSTR>(everyoneSid);
                    
                    PACL dacl = nullptr;
                    if (SetEntriesInAclW(1, &ea, nullptr, &dacl) == ERROR_SUCCESS) {
                        if (SetSecurityDescriptorDacl(&sd, TRUE, dacl, FALSE)) {
                            sa.nLength = sizeof(SECURITY_ATTRIBUTES);
                            sa.lpSecurityDescriptor = &sd;
                            sa.bInheritHandle = FALSE;
                            
                            pipe = CreateNamedPipeW(
                                kPipeName,
                                PIPE_ACCESS_DUPLEX,
                                PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                                PIPE_UNLIMITED_INSTANCES,
                                64 * 1024,
                                64 * 1024,
                                0,
                                &sa);
                            
                            LocalFree(dacl);
                        } else {
                            LocalFree(dacl);
                        }
                    }
                    FreeSid(everyoneSid);
                }
            }
            
            // If security setup failed, try with default security (nullptr)
            if (pipe == INVALID_HANDLE_VALUE) {
                pipe = CreateNamedPipeW(
                    kPipeName,
                    PIPE_ACCESS_DUPLEX,
                    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                    PIPE_UNLIMITED_INSTANCES,
                    64 * 1024,
                    64 * 1024,
                    0,
                    nullptr);
            }

            if (pipe == INVALID_HANDLE_VALUE) {
                const DWORD error = GetLastError();
                std::wstringstream ss;
                ss << L"CreateNamedPipe failed with error " << error;
                LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
                if (WaitForSingleObject(g_ctx.stopEvent, 2000) == WAIT_OBJECT_0) {
                    break;
                }
                continue;
            }

            // Wait for client connection (blocking)
            BOOL connected = ConnectNamedPipe(pipe, nullptr) ? TRUE : (GetLastError() == ERROR_PIPE_CONNECTED);
            if (!connected) {
                const DWORD error = GetLastError();
                if (error != ERROR_PIPE_CONNECTED) {
                    std::wstringstream ss;
                    ss << L"Worker thread " << id << L": ConnectNamedPipe failed with error " << error;
                    LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str(), error);
                }
                // Clean up failed pipe instance
                if (pipe != INVALID_HANDLE_VALUE) {
                    DisconnectNamedPipe(pipe);
                    CloseHandle(pipe);
                    pipe = INVALID_HANDLE_VALUE;
                }
                // Small delay before retrying to avoid tight loop
                if (WaitForSingleObject(g_ctx.stopEvent, 100) == WAIT_OBJECT_0) {
                    break;
                }
                continue;
            }

            std::wstringstream ss_conn;
            ss_conn << L"Worker thread " << id << L": Client connected to named pipe";
            LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss_conn.str());

            bool clientActive = true;
            while (clientActive && g_ctx.running) {
                try {
                    std::string payload;
                    if (!ReadPipeMessage(pipe, payload)) {
                        const DWORD error = GetLastError();
                        if (error != ERROR_BROKEN_PIPE && error != ERROR_PIPE_NOT_CONNECTED) {
                            std::wstringstream ss;
                            ss << L"ReadPipeMessage failed with error " << error;
                            LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str(), error);
                        }
                        clientActive = false;
                        break;
                    }

                    auto findCommand = [&](const std::string& json) -> std::string {
                        try {
                            const std::string key = "\"command\"";
                            const auto keyPos = json.find(key);
                            if (keyPos == std::string::npos) {
                                return {};
                            }
                            const auto colon = json.find(':', keyPos + key.size());
                            if (colon == std::string::npos) {
                                return {};
                            }
                            const auto firstQuote = json.find('"', colon + 1);
                            if (firstQuote == std::string::npos) {
                                return {};
                            }
                            const auto secondQuote = json.find('"', firstQuote + 1);
                            if (secondQuote == std::string::npos || secondQuote <= firstQuote) {
                                return {};
                            }
                            return json.substr(firstQuote + 1, secondQuote - firstQuote - 1);
                        } catch (const std::exception&) {
                            return {};
                        }
                    };

                    const std::string command = findCommand(payload);
                    std::string response;

                    try {
                        if (command == "ping") {
                            response = HandlePing();
                        } else if (command == "get_service_info") {
                            response = HandleGetServiceInfo();
                        } else if (command == "search_files") {
                            response = HandleSearchRequest(payload);
                        } else if (command.empty()) {
                            response = "{\"success\":false,\"error\":\"Invalid request: missing command\"}";
                            LogServiceEvent(EVENTLOG_WARNING_TYPE, L"Received request with missing or invalid command");
                        } else {
                            std::wstringstream ss;
                            ss << L"Unknown command received: ";
                            for (char c : command) {
                                ss << static_cast<wchar_t>(c);
                            }
                            LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str());
                            response = "{\"success\":false,\"error\":\"Unknown command\"}";
                        }
                    } catch (const std::exception& e) {
                        std::wstringstream ss;
                        ss << L"Exception handling command: ";
                        for (char c : std::string(e.what())) {
                            ss << static_cast<wchar_t>(c);
                        }
                        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
                        response = "{\"success\":false,\"error\":\"Internal error processing command\"}";
                    } catch (...) {
                        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception handling command");
                        response = "{\"success\":false,\"error\":\"Internal error processing command\"}";
                    }

                    if (!WritePipeMessage(pipe, response)) {
                        const DWORD error = GetLastError();
                        std::wstringstream ss;
                        ss << L"WritePipeMessage failed with error " << error;
                        LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str(), error);
                        clientActive = false;
                    }
                } catch (const std::exception& e) {
                    std::wstringstream ss;
                    ss << L"Exception in client message loop: ";
                    for (char c : std::string(e.what())) {
                        ss << static_cast<wchar_t>(c);
                    }
                    LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
                    clientActive = false;
                } catch (...) {
                    LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in client message loop");
                    clientActive = false;
                }
            }

            // Properly close and disconnect the pipe
            if (pipe != INVALID_HANDLE_VALUE) {
                HANDLE pipeToClose = pipe;
                pipe = INVALID_HANDLE_VALUE;  // Clear immediately to prevent reuse
                
                try {
                    // Flush any remaining data
                    FlushFileBuffers(pipeToClose);
                } catch (...) {
                    // Ignore flush errors - pipe may already be disconnected
                }
                
                try {
                    // Disconnect the pipe (allows new clients to connect to this instance)
                    DisconnectNamedPipe(pipeToClose);
                } catch (...) {
                    // Ignore disconnect errors - pipe may already be disconnected
                }
                
                // Always close the handle
                CloseHandle(pipeToClose);
                
                std::wstringstream ss3;
                ss3 << L"Worker thread " << id << L": Client disconnected, pipe closed and ready for next client";
                LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss3.str());
            }

            if (WaitForSingleObject(g_ctx.stopEvent, 0) == WAIT_OBJECT_0) {
                break;
            }
        }

        std::wstringstream ss2;
        ss2 << L"Service worker thread " << id << L" exiting normally";
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss2.str());
        return 0;
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in ServiceWorkerThread: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        return 1;
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in ServiceWorkerThread");
        return 1;
    }
}

}  // namespace

// Forward declaration
std::wstring FormatErrorMessage(DWORD error);

void LogServiceEvent(WORD level, const std::wstring& message, DWORD errorCode) {
    try {
        if (!g_ctx.eventSource) {
            g_ctx.eventSource = RegisterEventSourceW(nullptr, kServiceName);
        }

        if (!g_ctx.eventSource) {
            const DWORD regError = GetLastError();
            if (regError != ERROR_ACCESS_DENIED) {
                OutputDebugStringW((L"[FastSearch] Failed to register event source (error " + 
                    std::to_wstring(regError) + L"): " + message + L"\n").c_str());
            }
            return;
        }

        const wchar_t* strings[2] = { message.c_str(), nullptr };
        const WORD stringCount = 1;
        if (!ReportEventW(
                g_ctx.eventSource,
                level,
                0,
                0,
                nullptr,
                stringCount,
                errorCode != 0 ? sizeof(errorCode) : 0,
                strings,
                errorCode != 0 ? &errorCode : nullptr)) {
            const DWORD reportError = GetLastError();
            OutputDebugStringW((L"[FastSearch] Failed to report event (error " + 
                std::to_wstring(reportError) + L"): " + message + L"\n").c_str());
        }
    } catch (const std::exception&) {
        OutputDebugStringW((L"[FastSearch] Exception in LogServiceEvent: " + message + L"\n").c_str());
    } catch (...) {
        OutputDebugStringW(L"[FastSearch] Unknown exception in LogServiceEvent\n");
    }
}

void WINAPI ServiceCtrlHandler(DWORD control) {
    try {
        switch (control) {
            case SERVICE_CONTROL_STOP:
            case SERVICE_CONTROL_SHUTDOWN:
                LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Service stop requested");
                g_ctx.running = false;  // Signal all worker threads to stop
                ReportServiceStatus(SERVICE_STOP_PENDING, NO_ERROR, 0);
                if (g_ctx.stopEvent) {
                    if (!SetEvent(g_ctx.stopEvent)) {
                        const DWORD error = GetLastError();
                        std::wstringstream ss;
                        ss << L"SetEvent failed with error " << error;
                        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
                    }
                } else {
                    LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Stop event handle is null");
                }
                g_ctx.running = false;
                return;
            default:
                break;
        }
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in ServiceCtrlHandler: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in ServiceCtrlHandler");
    }
}

void WINAPI ServiceMain(DWORD argc, LPWSTR* argv) {
    DWORD exitCode = NO_ERROR;
    
    try {
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"ServiceMain called - service starting");

        g_ctx.statusHandle = RegisterServiceCtrlHandlerW(kServiceName, ServiceCtrlHandler);
        if (!g_ctx.statusHandle) {
            const DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"RegisterServiceCtrlHandler failed with error " << error;
            LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
            exitCode = error;
            return;
        }

        g_ctx.status.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
        g_ctx.status.dwServiceSpecificExitCode = 0;
        g_ctx.status.dwCheckPoint = 0;
        g_ctx.status.dwWaitHint = 0;

        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Service control handler registered successfully");
        ReportServiceStatus(SERVICE_START_PENDING);

        g_ctx.stopEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
        if (!g_ctx.stopEvent) {
            const DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"CreateEvent failed with error " << error;
            LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
            ReportServiceStatus(SERVICE_STOPPED, error);
            exitCode = error;
            return;
        }

        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Stop event created successfully");

        g_ctx.eventSource = RegisterEventSourceW(nullptr, kServiceName);
        if (!g_ctx.eventSource) {
            const DWORD error = GetLastError();
            std::wstringstream ss;
            ss << L"RegisterEventSource failed with error " << error;
            OutputDebugStringW(ss.str().c_str());
            ReportServiceStatus(SERVICE_STOPPED, error);
            CloseHandle(g_ctx.stopEvent);
            g_ctx.stopEvent = nullptr;
            exitCode = error;
            return;
        }

        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Event source registered successfully");

        g_ctx.running = true;
        
        // Create multiple worker threads for concurrent client support
        // Each thread manages one pipe instance
        // Create multiple worker threads for concurrent client support
        // Each thread manages one pipe instance, allowing up to NUM_WORKER_THREADS concurrent clients
        // Each thread creates a pipe instance, waits for connection, processes requests, then closes and repeats
        const DWORD NUM_WORKER_THREADS = 20;  // Increased from 10 to support more concurrent clients
        g_ctx.workerThreadCount = NUM_WORKER_THREADS;
        g_ctx.workerThreads = new HANDLE[NUM_WORKER_THREADS];
        
        bool allThreadsCreated = true;
        for (DWORD i = 0; i < NUM_WORKER_THREADS; ++i) {
            g_ctx.workerThreads[i] = CreateThread(
                nullptr, 
                0, 
                ServiceWorkerThread, 
                reinterpret_cast<LPVOID>(static_cast<DWORD_PTR>(i)), 
                0, 
                nullptr
            );
            if (!g_ctx.workerThreads[i]) {
                const DWORD error = GetLastError();
                std::wstringstream ss;
                ss << L"CreateThread failed for worker " << i << L" with error " << error;
                LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str(), error);
                allThreadsCreated = false;
                // Close already created threads
                for (DWORD j = 0; j < i; ++j) {
                    if (g_ctx.workerThreads[j]) {
                        CloseHandle(g_ctx.workerThreads[j]);
                    }
                }
                delete[] g_ctx.workerThreads;
                g_ctx.workerThreads = nullptr;
                g_ctx.workerThreadCount = 0;
                break;
            }
        }
        
        if (!allThreadsCreated) {
            ReportServiceStatus(SERVICE_STOPPED, GetLastError());
            CloseHandle(g_ctx.stopEvent);
            g_ctx.stopEvent = nullptr;
            DeregisterEventSource(g_ctx.eventSource);
            g_ctx.eventSource = nullptr;
            exitCode = GetLastError();
            return;
        }

        std::wstringstream ss;
        ss << L"Created " << NUM_WORKER_THREADS << L" worker threads successfully";
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss.str());
        ReportServiceStatus(SERVICE_RUNNING);
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Service is now running");

        WaitForSingleObject(g_ctx.stopEvent, INFINITE);
        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Stop event signaled - shutting down");

        // Wait for all worker threads to exit
        if (g_ctx.workerThreads && g_ctx.workerThreadCount > 0) {
            const DWORD waitResult = WaitForMultipleObjects(
                g_ctx.workerThreadCount,
                g_ctx.workerThreads,
                TRUE,  // Wait for all threads
                5000   // 5 second timeout
            );
            
            if (waitResult == WAIT_TIMEOUT) {
                LogServiceEvent(EVENTLOG_WARNING_TYPE, L"Some worker threads did not exit within timeout");
                // Terminate any remaining threads
                for (DWORD i = 0; i < g_ctx.workerThreadCount; ++i) {
                    if (g_ctx.workerThreads[i]) {
                        DWORD exitCode = 0;
                        if (GetExitCodeThread(g_ctx.workerThreads[i], &exitCode) && exitCode == STILL_ACTIVE) {
                            TerminateThread(g_ctx.workerThreads[i], 1);
                        }
                    }
                }
            } else {
                std::wstringstream ss;
                ss << L"All " << g_ctx.workerThreadCount << L" worker threads exited successfully";
                LogServiceEvent(EVENTLOG_INFORMATION_TYPE, ss.str());
            }
            
            // Close all thread handles
            for (DWORD i = 0; i < g_ctx.workerThreadCount; ++i) {
                if (g_ctx.workerThreads[i]) {
                    CloseHandle(g_ctx.workerThreads[i]);
                }
            }
            delete[] g_ctx.workerThreads;
            g_ctx.workerThreads = nullptr;
            g_ctx.workerThreadCount = 0;
        }

        if (g_ctx.stopEvent) {
            CloseHandle(g_ctx.stopEvent);
            g_ctx.stopEvent = nullptr;
        }

        if (g_ctx.eventSource) {
            DeregisterEventSource(g_ctx.eventSource);
            g_ctx.eventSource = nullptr;
        }

        LogServiceEvent(EVENTLOG_INFORMATION_TYPE, L"Service shutdown complete");
        ReportServiceStatus(SERVICE_STOPPED, exitCode);
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in ServiceMain: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        exitCode = ERROR_EXCEPTION_IN_SERVICE;
        if (g_ctx.statusHandle) {
            ReportServiceStatus(SERVICE_STOPPED, exitCode);
        }
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in ServiceMain");
        exitCode = ERROR_EXCEPTION_IN_SERVICE;
        if (g_ctx.statusHandle) {
            ReportServiceStatus(SERVICE_STOPPED, exitCode);
        }
    }
}

bool ReadPipeMessage(HANDLE pipe, std::string& payload) {
    try {
        if (pipe == INVALID_HANDLE_VALUE || pipe == nullptr) {
            return false;
        }

        DWORD readBytes = 0;
        uint32_t length = 0;
        if (!ReadFile(pipe, &length, sizeof(length), &readBytes, nullptr) || readBytes != sizeof(length)) {
            return false;
        }

        if (length == 0 || length > (64 * 1024)) {
            std::wstringstream ss;
            ss << L"Invalid message length: " << length;
            LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str());
            return false;
        }

        std::vector<char> buffer(length);
        if (!ReadFile(pipe, buffer.data(), length, &readBytes, nullptr) || readBytes != length) {
            return false;
        }

        payload.assign(buffer.begin(), buffer.end());
        return true;
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in ReadPipeMessage: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        return false;
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in ReadPipeMessage");
        return false;
    }
}

bool WritePipeMessage(HANDLE pipe, const std::string& payload) {
    try {
        if (pipe == INVALID_HANDLE_VALUE || pipe == nullptr) {
            return false;
        }

        const uint32_t length = static_cast<uint32_t>(payload.size());
        DWORD written = 0;
        if (!WriteFile(pipe, &length, sizeof(length), &written, nullptr) || written != sizeof(length)) {
            return false;
        }
        if (length == 0) {
            return true;
        }
        if (!WriteFile(pipe, payload.data(), length, &written, nullptr) || written != length) {
            return false;
        }
        if (!FlushFileBuffers(pipe)) {
            const DWORD error = GetLastError();
            if (error != ERROR_BROKEN_PIPE) {
                std::wstringstream ss;
                ss << L"FlushFileBuffers failed with error " << error;
                LogServiceEvent(EVENTLOG_WARNING_TYPE, ss.str(), error);
            }
        }
        return true;
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in WritePipeMessage: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        return false;
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in WritePipeMessage");
        return false;
    }
}

std::string HandlePing() {
    try {
        return "{\"success\":true,\"message\":\"pong\"}";
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in HandlePing: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        return "{\"success\":false,\"error\":\"Internal error\"}";
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in HandlePing");
        return "{\"success\":false,\"error\":\"Internal error\"}";
    }
}

std::string HandleGetServiceInfo() {
    try {
        std::ostringstream ss;
        ss << "{\"success\":true,\"info\":{"
           << "\"service\":\"FastSearch MCP\",";

        auto now = std::chrono::system_clock::now();
        auto nowTime = std::chrono::system_clock::to_time_t(now);
        ss << "\"timestamp\":" << static_cast<long long>(nowTime) << ','
           << "\"pipe\":\"\\\\\\\\.\\\\pipe\\\\FastSearchMCP\"}}";
        return ss.str();
    } catch (const std::exception& e) {
        std::wstringstream ss;
        ss << L"Exception in HandleGetServiceInfo: ";
        for (char c : std::string(e.what())) {
            ss << static_cast<wchar_t>(c);
        }
        LogServiceEvent(EVENTLOG_ERROR_TYPE, ss.str());
        return "{\"success\":false,\"error\":\"Internal error\"}";
    } catch (...) {
        LogServiceEvent(EVENTLOG_ERROR_TYPE, L"Unknown exception in HandleGetServiceInfo");
        return "{\"success\":false,\"error\":\"Internal error\"}";
    }
}

// HandleSearchRequest is now implemented in mft_search.cpp
// Forward declaration
std::string HandleSearchRequestImpl(const std::string& requestJson);

std::string HandleSearchRequest(const std::string& requestJson) {
    return HandleSearchRequestImpl(requestJson);
}

bool InstallService() {
    wchar_t path[MAX_PATH] = {};
    if (!GetModuleFileNameW(nullptr, path, MAX_PATH)) {
        const DWORD error = GetLastError();
        std::wcerr << L"GetModuleFileName failed: " << FormatErrorMessage(error);
        return false;
    }

    SC_HANDLE scm = OpenSCManagerW(nullptr, nullptr, SC_MANAGER_ALL_ACCESS);
    if (!scm) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenSCManager failed: " << FormatErrorMessage(error);
        return false;
    }

    SC_HANDLE service = CreateServiceW(
        scm,
        kServiceName,
        kServiceDisplayName,
        SERVICE_ALL_ACCESS,
        SERVICE_WIN32_OWN_PROCESS,
        SERVICE_AUTO_START,
        SERVICE_ERROR_NORMAL,
        path,
        nullptr,
        nullptr,
        nullptr,
        nullptr,
        nullptr);

    if (!service) {
        const DWORD error = GetLastError();
        std::wcerr << L"CreateService failed: " << FormatErrorMessage(error);
        CloseServiceHandle(scm);
        return false;
    }

    SERVICE_DESCRIPTIONW description{};
    description.lpDescription = const_cast<LPWSTR>(kServiceDescription);
    ChangeServiceConfig2W(service, SERVICE_CONFIG_DESCRIPTION, &description);

    CloseServiceHandle(service);
    CloseServiceHandle(scm);
    std::wcout << L"Service installed successfully." << std::endl;
    return true;
}

bool UninstallService() {
    SC_HANDLE scm = OpenSCManagerW(nullptr, nullptr, SC_MANAGER_ALL_ACCESS);
    if (!scm) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenSCManager failed: " << FormatErrorMessage(error);
        return false;
    }

    SC_HANDLE service = OpenServiceW(scm, kServiceName, DELETE | SERVICE_STOP | SERVICE_QUERY_STATUS);
    if (!service) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenService failed: " << FormatErrorMessage(error);
        CloseServiceHandle(scm);
        return false;
    }

    SERVICE_STATUS_PROCESS status{};
    DWORD bytesNeeded = 0;
    if (QueryServiceStatusEx(service, SC_STATUS_PROCESS_INFO, reinterpret_cast<LPBYTE>(&status), sizeof(status), &bytesNeeded)) {
        if (status.dwCurrentState != SERVICE_STOPPED) {
            ControlService(service, SERVICE_CONTROL_STOP, reinterpret_cast<LPSERVICE_STATUS>(&status));
            Sleep(2000);
        }
    }

    const BOOL deleted = DeleteService(service);
    const DWORD error = deleted ? ERROR_SUCCESS : GetLastError();
    CloseServiceHandle(service);
    CloseServiceHandle(scm);

    if (!deleted) {
        std::wcerr << L"DeleteService failed: " << FormatErrorMessage(error);
        return false;
    }

    std::wcout << L"Service uninstalled successfully." << std::endl;
    return true;
}

bool StartExistingService() {
    SC_HANDLE scm = OpenSCManagerW(nullptr, nullptr, SC_MANAGER_ALL_ACCESS);
    if (!scm) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenSCManager failed: " << FormatErrorMessage(error);
        return false;
    }

    SC_HANDLE service = OpenServiceW(scm, kServiceName, SERVICE_START);
    if (!service) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenService failed: " << FormatErrorMessage(error);
        CloseServiceHandle(scm);
        return false;
    }

    const BOOL started = StartServiceW(service, 0, nullptr);
    const DWORD error = started ? ERROR_SUCCESS : GetLastError();
    CloseServiceHandle(service);
    CloseServiceHandle(scm);

    if (!started && error != ERROR_SERVICE_ALREADY_RUNNING) {
        std::wcerr << L"StartService failed: " << FormatErrorMessage(error);
        return false;
    }

    std::wcout << L"Service start command issued." << std::endl;
    return true;
}

bool StopExistingService() {
    SC_HANDLE scm = OpenSCManagerW(nullptr, nullptr, SC_MANAGER_ALL_ACCESS);
    if (!scm) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenSCManager failed: " << FormatErrorMessage(error);
        return false;
    }

    SC_HANDLE service = OpenServiceW(scm, kServiceName, SERVICE_STOP | SERVICE_QUERY_STATUS);
    if (!service) {
        const DWORD error = GetLastError();
        std::wcerr << L"OpenService failed: " << FormatErrorMessage(error);
        CloseServiceHandle(scm);
        return false;
    }

    SERVICE_STATUS status{};
    const BOOL stopped = ControlService(service, SERVICE_CONTROL_STOP, &status);
    const DWORD error = stopped ? ERROR_SUCCESS : GetLastError();
    CloseServiceHandle(service);
    CloseServiceHandle(scm);

    if (!stopped && error != ERROR_SERVICE_NOT_ACTIVE) {
        std::wcerr << L"ControlService failed: " << FormatErrorMessage(error);
        return false;
    }

    std::wcout << L"Service stop command issued." << std::endl;
    return true;
}

void PrintUsage() {
    std::wcout << L"FastSearch MCP Service" << std::endl
               << L"Usage: fastsearchservice [--install|--uninstall|--start|--stop|--help]" << std::endl;
}

std::wstring FormatErrorMessage(DWORD error) {
    LPWSTR buffer = nullptr;
    const DWORD len = FormatMessageW(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr,
        error,
        0,
        reinterpret_cast<LPWSTR>(&buffer),
        0,
        nullptr);
    std::wstring message;
    if (len > 0 && buffer) {
        message.assign(buffer, len);
        LocalFree(buffer);
    }
    return message;
}

int wmain(int argc, wchar_t* argv[]) {
    g_ctx.status = {};

    if (argc > 1) {
        const std::wstring command = argv[1];
        if (command == L"--install") {
            return InstallService() ? 0 : 1;
        }
        if (command == L"--uninstall") {
            return UninstallService() ? 0 : 1;
        }
        if (command == L"--start") {
            return StartExistingService() ? 0 : 1;
        }
        if (command == L"--stop") {
            return StopExistingService() ? 0 : 1;
        }
        PrintUsage();
        return 0;
    }

    SERVICE_TABLE_ENTRYW dispatchTable[] = {
        { const_cast<LPWSTR>(kServiceName), ServiceMain },
        { nullptr, nullptr }
    };

    if (!StartServiceCtrlDispatcherW(dispatchTable)) {
        const DWORD error = GetLastError();
        std::wstringstream ss;
        ss << L"StartServiceCtrlDispatcher failed with error " << error;
        std::wcout << ss.str() << std::endl;
        OutputDebugStringW((ss.str() + L"\n").c_str());
        
        HANDLE eventSource = RegisterEventSourceW(nullptr, kServiceName);
        if (eventSource) {
            const wchar_t* strings[] = { ss.str().c_str() };
            DWORD errorCode = error;
            ReportEventW(eventSource, EVENTLOG_ERROR_TYPE, 0, 0, nullptr, 1, sizeof(errorCode), strings, &errorCode);
            DeregisterEventSource(eventSource);
        }
        
        return static_cast<int>(error);
    }

    return 0;
}
