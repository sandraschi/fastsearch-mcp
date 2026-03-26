cmake_minimum_required(VERSION 3.10)

# Check for C++ compiler before project() call
if(WIN32)
    # On Windows, prefer MSVC compiler (Visual Studio)
    if(NOT DEFINED ENV{VCINSTALLDIR} AND NOT DEFINED CMAKE_CXX_COMPILER)
        message(WARNING "Visual Studio environment not detected.")
        message(WARNING "Please either:")
        message(WARNING "  1. Run from 'Visual Studio Developer Command Prompt', OR")
        message(WARNING "  2. Run: \"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat\", OR")
        message(WARNING "  3. Use one of the build scripts: build.bat, build_all.ps1, or build-installer.ps1")
    endif()
endif()

project(FastSearchService VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Set include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}
)

# Set Windows SDK version
if(WIN32)
    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(CMAKE_CXX_EXTENSIONS OFF)
    
    # Set Windows SDK version if not specified
    if(NOT CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION)
        set(CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION "10.0.19041.0")
    endif()
    
    add_definitions(-D_WIN32_WINNT=0x0601)  # Windows 7 or later
    add_definitions(-DUNICODE -D_UNICODE)
endif()

# Add the service executable
add_executable(FastSearchServiceNew
    src/fastsearch_service.cpp
    src/mft_search.cpp
    include/fastsearch_service.h
)

# Set Windows version target
if(WIN32)
    add_compile_definitions(_WIN32_WINNT=0x0601)  # Target Windows 7 or later
    add_compile_definitions(UNICODE _UNICODE)
    
    # Link Windows libraries
    target_link_libraries(FastSearchServiceNew
        PRIVATE
            advapi32.lib
            shell32.lib
            user32.lib
            aclui.lib
    )
    
    # Set Windows SDK version if not specified
    if(NOT CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION)
        set(CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION "10.0.19041.0")
    endif()
endif()

# Installation
install(TARGETS FastSearchServiceNew
    RUNTIME DESTINATION bin
    CONFIGURATIONS Release
)

# CPack configuration for MSI installer
set(CPACK_GENERATOR "WIX")
set(CPACK_PACKAGE_NAME "FastSearchMCP")
set(CPACK_PACKAGE_VENDOR "sandraschi")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "FastSearch MCP - High-performance NTFS file search with Claude Desktop integration")
set(CPACK_PACKAGE_DESCRIPTION "FastSearch MCP provides lightning-fast file search using direct NTFS MFT access via C++ service with Python MCP bridge")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "FastSearch MCP")
set(CPACK_PACKAGE_INSTALL_REGISTRY_KEY "FastSearchMCP")

# MSI-specific settings
set(CPACK_WIX_PRODUCT_GUID "3298de23-b4e3-481e-91f7-ddcb238b95b4")
set(CPACK_WIX_UPGRADE_GUID "3298de23-b4e3-481e-91f7-ddcb238b95b4")
set(CPACK_WIX_PROPERTY_ARPURLINFOABOUT "https://github.com/sandraschi/fastsearch-mcp")
set(CPACK_WIX_PROPERTY_ARPHELPLINK "https://github.com/sandraschi/fastsearch-mcp/issues")
set(CPACK_WIX_CMAKE_PACKAGE_REGISTRY ON)
set(CPACK_WIX_PROPERTY_ARPCONTACT "team@sandraschi.dev")

# Service installation (requires custom WiX fragment)
# Note: CPack doesn't natively support Windows Service installation
# We'll need to add a custom WiX fragment for service installation
set(CPACK_WIX_EXTRA_SOURCES "${CMAKE_SOURCE_DIR}/../wix/ServiceFragment.wxs")

# License file (if exists)
if(EXISTS "${CMAKE_SOURCE_DIR}/../LICENSE")
    set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/../LICENSE")
endif()

# Package file name
set(CPACK_PACKAGE_FILE_NAME "FastSearchMCP-${PROJECT_VERSION}-windows-x64")

include(CPack)
