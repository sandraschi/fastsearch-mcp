# Visual Studio Debugger Setup for FastSearch Service

## 🎯 Purpose
- Document the approved Visual Studio workflow for debugging the C++ Windows service without violating FastSearch architecture guardrails.
- Provide step-by-step install and attach guidance for developers and AI assistants.

## 🚀 Install Visual Studio Community 2022
> Shortcut: run `.\scripts\install-visualstudio-community.ps1` from an elevated PowerShell prompt to automate the download and installation with the correct workload and components.

1. Download the free Community edition manually from <https://visualstudio.microsoft.com/vs/community/> (skip if using the script above).
2. Run the installer and select the `Desktop development with C++` workload.
3. Confirm the following optional components stay checked:
   - Windows 10/11 SDK (latest installed version).
   - C++ CMake tools for Windows.
   - C++ Clang tools for Windows (optional but helpful for static analysis).
4. Finish installation and launch the `x64 Native Tools Command Prompt for VS 2022` once to register environment variables.

> ✅ Visual Studio Community is free for individual developers, open-source projects, and small teams. Larger organizations need to confirm licensing.

## 🛠 Prepare the Service Build
1. From the repository root, open `service\FastSearchService.sln` in Visual Studio.
2. Set the solution configuration to `Debug` and platform to `x64`.
3. Run `Build > Build Solution` (or press `Ctrl+Shift+B`).
4. Verify the debug binary appears at `service\build\bin\Debug\FastSearchServiceNew.exe`.

## 🧩 Attaching the Debugger to the Service
1. Install/start the service using the provided PowerShell scripts (must run elevated):
   - `.\\install-service.ps1 install`
   - `.\\install-service.ps1 start`
2. In Visual Studio, choose `Debug > Attach to Process…`.
3. Enable `Show processes from all users` and `Show processes in all sessions`.
4. Select `FastSearchServiceNew.exe`, ensure `Attach to:` displays `Native Code`, then click `Attach`.
5. Set breakpoints in `service\src\fastsearch_service.cpp` or other relevant files.
6. Trigger the scenario (e.g., run a search via the MCP bridge) and inspect hits.

## ⚡ Capturing Startup Failures
- Startup crashes (Event ID 7034) require catching the process immediately after launch.
- Option A: Use `Debug > Attach to Process…`, check `Attach to: Native Code`, then run `.\\install-service.ps1 start`. Visual Studio will break on the exception once the service spawns.
- Option B: If available, run the binary directly in foreground mode (`FastSearchServiceNew.exe --run-foreground`) from an elevated PowerShell session and press `F5` in Visual Studio to start debugging.

## 🔍 Diagnostics & Logs
- Always review Event Viewer: `Applications and Services Logs → FastSearchMCP` for initialization failures.
- Use repository helpers such as `.\\debug-service-startup.ps1` and `.\\scripts\\read-service-logs.ps1` to gather supporting data.
- Capture call stacks and module loads before filing issues.

## 🚨 Architecture Guardrails (Non-Negotiable)
- The debugger workflow must NEVER introduce background indexing, in-memory file caches, or persistence layers.
- Always validate that fixes preserve direct NTFS MFT access, max-results early termination, and zero indexing behavior.
- Reference the WizFile comparison if collaborators push for caching or preload optimizations—those are forbidden.

## 📝 Maintenance Notes
- Update this document whenever Visual Studio installer options or service debugging steps change.
- Cross-link with `docs/DEVELOPMENT.md` (Debugging → C++ service) if instructions diverge so both stay consistent.
- Record significant debugging discoveries in `docs/SERVICE_DEVELOPMENT_STATUS.md`.

