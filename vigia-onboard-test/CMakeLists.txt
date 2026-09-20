cmake_minimum_required(VERSION 3.21)
project(vigia-capture-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# OpenCV via Conan (CMakeDeps + CMakeToolchain).
find_package(OpenCV REQUIRED COMPONENTS core imgproc highgui videoio imgcodecs)

# ---------------------------------------------------------------------------
# ONNX Runtime: binário oficial (Conan recipe compila do fonte ~horas).
# ONNXRUNTIME_ROOT ou download automático Windows/Linux x64.
# ---------------------------------------------------------------------------
set(ONNXRUNTIME_VERSION "1.20.1" CACHE STRING "ONNX Runtime version to fetch")
set(ONNXRUNTIME_ROOT "" CACHE PATH "Path to a local ONNX Runtime install (include/ + lib/)")

function(vigia_setup_onnxruntime)
  if(ONNXRUNTIME_ROOT AND EXISTS "${ONNXRUNTIME_ROOT}/include/onnxruntime_cxx_api.h")
    set(ORT_INCLUDE_DIR "${ONNXRUNTIME_ROOT}/include" PARENT_SCOPE)
    if(WIN32)
      set(ORT_LIB "${ONNXRUNTIME_ROOT}/lib/onnxruntime.lib" PARENT_SCOPE)
      set(ORT_DLL "${ONNXRUNTIME_ROOT}/lib/onnxruntime.dll" PARENT_SCOPE)
    else()
      find_library(ORT_LIB_FOUND onnxruntime PATHS "${ONNXRUNTIME_ROOT}/lib" REQUIRED)
      set(ORT_LIB "${ORT_LIB_FOUND}" PARENT_SCOPE)
    endif()
    message(STATUS "ONNX Runtime (local): ${ONNXRUNTIME_ROOT}")
    return()
  endif()

  set(ORT_CACHE_DIR "${CMAKE_BINARY_DIR}/_deps/onnxruntime")
  if(WIN32)
    set(ORT_URL
      "https://github.com/microsoft/onnxruntime/releases/download/v${ONNXRUNTIME_VERSION}/onnxruntime-win-x64-${ONNXRUNTIME_VERSION}.zip")
    set(ORT_EXTRACT_NAME "onnxruntime-win-x64-${ONNXRUNTIME_VERSION}")
  elseif(UNIX AND NOT APPLE)
    set(ORT_URL
      "https://github.com/microsoft/onnxruntime/releases/download/v${ONNXRUNTIME_VERSION}/onnxruntime-linux-x64-${ONNXRUNTIME_VERSION}.tgz")
    set(ORT_EXTRACT_NAME "onnxruntime-linux-x64-${ONNXRUNTIME_VERSION}")
  else()
    message(FATAL_ERROR
      "Download automático de ONNX Runtime não configurado para esta plataforma. "
      "Defina -DONNXRUNTIME_ROOT=/path/to/onnxruntime")
  endif()

  set(ORT_HOME "${ORT_CACHE_DIR}/${ORT_EXTRACT_NAME}")
  if(NOT EXISTS "${ORT_HOME}/include/onnxruntime_cxx_api.h")
    message(STATUS "A descarregar ONNX Runtime ${ONNXRUNTIME_VERSION}…")
    file(MAKE_DIRECTORY "${ORT_CACHE_DIR}")
    set(ORT_ARCHIVE "${ORT_CACHE_DIR}/ort-download")
    if(WIN32)
      set(ORT_ARCHIVE "${ORT_ARCHIVE}.zip")
    else()
      set(ORT_ARCHIVE "${ORT_ARCHIVE}.tgz")
    endif()
    file(DOWNLOAD "${ORT_URL}" "${ORT_ARCHIVE}" SHOW_PROGRESS STATUS _dl_status)
    list(GET _dl_status 0 _dl_code)
    if(NOT _dl_code EQUAL 0)
      message(FATAL_ERROR "Falha ao descarregar ONNX Runtime: ${_dl_status}")
    endif()
    file(ARCHIVE_EXTRACT INPUT "${ORT_ARCHIVE}" DESTINATION "${ORT_CACHE_DIR}")
  endif()

  set(ORT_INCLUDE_DIR "${ORT_HOME}/include" PARENT_SCOPE)
  if(WIN32)
    set(ORT_LIB "${ORT_HOME}/lib/onnxruntime.lib" PARENT_SCOPE)
    set(ORT_DLL "${ORT_HOME}/lib/onnxruntime.dll" PARENT_SCOPE)
  else()
    set(ORT_LIB "${ORT_HOME}/lib/libonnxruntime.so" PARENT_SCOPE)
  endif()
  message(STATUS "ONNX Runtime (fetched): ${ORT_HOME}")
endfunction()

vigia_setup_onnxruntime()

add_executable(vigia-capture-cpp
  main.cpp
  src/settings.cpp
  src/capture_runner.cpp
  src/yolo_pose.cpp
  src/yolo_session.cpp
)

target_include_directories(vigia-capture-cpp PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${ORT_INCLUDE_DIR}
)

target_link_libraries(vigia-capture-cpp PRIVATE
  opencv::opencv
  ${ORT_LIB}
)

if(MSVC)
  target_compile_options(vigia-capture-cpp PRIVATE /W4 /EHsc /utf-8)
  target_compile_definitions(vigia-capture-cpp PRIVATE _CRT_SECURE_NO_WARNINGS)
else()
  target_compile_options(vigia-capture-cpp PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(WIN32)
  set(_runtime_copy_cmds)
  if(DEFINED ORT_DLL AND EXISTS "${ORT_DLL}")
    list(APPEND _runtime_copy_cmds
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${ORT_DLL}"
        $<TARGET_FILE_DIR:vigia-capture-cpp>
    )
  endif()
  list(APPEND _runtime_copy_cmds
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
      $<TARGET_RUNTIME_DLLS:vigia-capture-cpp>
      $<TARGET_FILE_DIR:vigia-capture-cpp>
    COMMAND_EXPAND_LISTS
  )
  add_custom_command(TARGET vigia-capture-cpp POST_BUILD
    ${_runtime_copy_cmds}
    COMMENT "A copiar DLLs de runtime (OpenCV/ORT) para o diretório do executável"
  )
endif()
