cmake_minimum_required(VERSION 3.10)
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
add_executable(FastSearchService
    src/fastsearch_service.cpp
    include/fastsearch_service.h
)

# Set Windows version target
if(WIN32)
    add_compile_definitions(_WIN32_WINNT=0x0601)  # Target Windows 7 or later
    add_compile_definitions(UNICODE _UNICODE)
    
    # Link Windows libraries
    target_link_libraries(FastSearchService
        PRIVATE
            advapi32.lib
            shell32.lib
            user32.lib
    )
    
    # Set Windows SDK version if not specified
    if(NOT CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION)
        set(CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION "10.0.19041.0")
    endif()
endif()

# Installation
install(TARGETS FastSearchService
    RUNTIME DESTINATION bin
    CONFIGURATIONS Release
)

# Create an installer package using CPack
set(CPACK_PACKAGE_NAME "FastSearchMCP")
set(CPACK_PACKAGE_VERSION "1.0.0")
set(CPACK_PACKAGE_VENDOR "Your Company")
set(CPACK_PACKAGE_DESCRIPTION "FastSearch MCP Windows Service")
set(CPACK_PACKAGE_EXECUTABLES "FastSearchService" "FastSearch MCP Service")
set(CPACK_NSIS_MUI_ICON "${CMAKE_SOURCE_DIR}/assets/icon.ico")
set(CPACK_NSIS_DISPLAY_NAME "FastSearch MCP Service")
set(CPACK_NSIS_INSTALLED_ICON_NAME "bin\\FastSearchService.exe")
set(CPACK_NSIS_HELP_LINK "https://your-company.com/support")
set(CPACK_NSIS_URL_INFO_ABOUT "https://your-company.com")
set(CPACK_NSIS_MODIFY_PATH ON)

include(CPack)
