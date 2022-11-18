include(FindPkgConfig)
if(NOT PKG_CONFIG_FOUND)
    message(STATUS "pkgconf not found")
    return()
endif()

pkg_check_modules(ZMQ libzmq)
if(NOT ZMQ_FOUND)
    message(STATUS "zeromq not found")
    return()
endif()

find_library(ZMQPP_LIBRARIES NAMES zmqpp HINTS /usr/lib/x86_64-linux-gnu/)

if(NOT ZMQPP_LIBRARIES)
    message(STATUS "zeromqpp not found")
    return()
endif()

find_package(Protobuf 3.0.0)
if(NOT Protobuf_FOUND)
    message(STATUS "protobuf not found")
  return()
endif()

check_include_file_cxx(stdint.h HAVE_STDINT_H)
if(HAVE_STDINT_H)
    add_definitions(-DHAVE_STDINT_H)
endif()

set(examples_as_tests_sources)
if(${ENABLE_EXAMPLES})
    set(examples_as_tests_sources    
        #test/netsim-interface-examples-test-suite.cc
        )
endif()    

set(proto_source_files
    ${PROJECT_SOURCE_DIR}/../../../messages/netsimInterfaceMsgs.proto
)
include_directories(${Protobuf_INCLUDE_DIRS})
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${proto_source_files})
file(RELATIVE_PATH PROTO_HDRS_REL ${CMAKE_CURRENT_SOURCE_DIR} ${PROTO_HDRS})

build_lib(
    LIBNAME netsim-interface
    SOURCE_FILES model/netsim-interface.cc
                 model/wave_server.cc
                 helper/netsim-interface-helper.cc 
                 ${PROTO_SRCS}
    HEADER_FILES model/netsim-interface.h
                 model/wave_server.h
                 helper/netsim-interface-helper.h
                 ${PROTO_HDRS_REL}
    LIBRARIES_TO_LINK 
        ${libcore}
        ${libmobility}
        ${ZMQ_LIBRARIES}
        ${ZMQPP_LIBRARIES}
        ${Protobuf_LIBRARIES}
        ${libwifi}
        ${libinternet}
        ${libwave}
        ${libflow-monitor}
    TEST_SOURCES test/netsim-interface-test-suite.cc
                 ${examples_as_tests_sources}
)
    
