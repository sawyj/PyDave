cmake_minimum_required(VERSION 3.20)
project(pydave_external_sender LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
  add_compile_options(/W4 /WX)
  add_definitions(-DWINDOWS)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

find_package(MLSPP CONFIG REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(nlohmann_json REQUIRED)

add_library(pydave_external_sender SHARED
  G:/PyDAVE/vendor/libdave/cpp/test/external_sender.cpp
  G:/PyDAVE/vendor/libdave/cpp/test/capi/external_sender_wrapper.cpp
  G:/PyDAVE/native_helpers/external_sender/memory_bridge.cpp
)

target_include_directories(pydave_external_sender PRIVATE
  G:/PyDAVE/vendor/libdave/cpp/includes
  G:/PyDAVE/vendor/libdave/cpp/src
  G:/PyDAVE/vendor/libdave/cpp/test
  G:/PyDAVE/vendor/libdave/cpp/test/capi
)

target_link_libraries(pydave_external_sender PRIVATE
  G:/PyDAVE/build/cpp/Release/libdave.lib
  MLSPP::bytes
  MLSPP::mlspp
  OpenSSL::Crypto
  ws2_32
  crypt32
)
