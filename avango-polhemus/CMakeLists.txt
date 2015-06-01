cmake_minimum_required(VERSION 2.8.0)
project(AVANGO_POLHEMUS CXX)
set(CMAKE_CONFIGURATION_TYPES "Debug;Release" CACHE STRING "" FORCE)
if (UNIX)
  find_package(PkgConfig)
endif(UNIX)

set(CMAKE_CXX_FLAGS "-std=c++0x")

if (UNIX)
    set(CMAKE_CXX_FLAGS_RELEASE "-s -O4 --std=c++0x")
    set(CMAKE_CXX_FLAGS_DEBUG "-g -Wall --std=c++0x")
elseif(MSVC)
    set(CMAKE_CXX_FLAGS_RELEASE "-D NDEBUG -D _SECURE_SCL=0 -D _SCL_SECURE_NO_WARNINGS -D _CRT_SECURE_NO_DEPRECATE /MD /MP")
    set(CMAKE_CXX_FLAGS_DEBUG "-D_DEBUG /MDd /Zi")
    add_definitions(-D AV_INSTANTIATE_FIELD_TEMPLATES -D NOMINMAX)
endif(UNIX)

link_directories(
  /opt/guacamole/new_renderer/install/lib
  /opt/avango/new_renderer/lib
  )

include_directories(
  /opt/avango/new_renderer/avango-core/include
  /opt/avango/new_renderer/avango-python/include
  /opt/avango/new_renderer/avango-daemon/include
  /opt/guacamole/new_renderer/install/include
  /opt/boost/latest/include
  include
  /opt/schism/current/scm_core/src
  /opt/schism/current/scm_gl_core/src
  /opt/schism/current/scm_gl_util
)

add_library(avango_polhemus SHARED
  src/polhemus/PiTracker.cpp
  src/polhemus/PingPong.cpp
  src/polhemus/liberty.cpp
  src/Polhemus.cpp
  )

target_link_libraries(avango_polhemus
  debug avango_script avango avango_daemon usb-1.0 ${LIBRARIES}
  optimized avango_script avango avango_daemon usb-1.0 ${LIBRARIES})

add_subdirectory(python)
