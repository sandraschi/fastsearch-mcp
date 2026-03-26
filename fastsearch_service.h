#pragma once

// Windows target definitions
#ifndef WINVER
#define WINVER 0x0601
#endif
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0601
#endif

#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <string>
#include <vector>

// Service metadata
constexpr wchar_t kServiceName[] = L"FastSearchMCP";
constexpr wchar_t kServiceDisplayName[] = L"FastSearch MCP Service";
constexpr wchar_t kServiceDescription[] = L"Provides direct NTFS MFT search via named pipe";
constexpr wchar_t kPipeName[] = L"\\\\.\\pipe\\FastSearchMCP";

// Logging helpers
void LogServiceEvent(WORD level, const std::wstring& message, DWORD errorCode = 0);

// Service lifecycle
void WINAPI ServiceMain(DWORD argc, LPWSTR* argv);
void WINAPI ServiceCtrlHandler(DWORD control);

// Utility helpers
bool ReadPipeMessage(HANDLE pipe, std::string& payload);
bool WritePipeMessage(HANDLE pipe, const std::string& payload);

// Search processing
std::string HandlePing();
std::string HandleGetServiceInfo();
std::string HandleSearchRequest(const std::string& requestJson);
