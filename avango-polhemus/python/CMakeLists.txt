set(Python_ADDITIONAL_VERSIONS 3.4)
find_package(PythonLibs 3 REQUIRED)
find_package(Boost COMPONENTS python3 REQUIRED)

include_directories(${PYTHON_INCLUDE_DIRS})
include_directories(${Boost_INCLUDE_DIRS})

link_directories(
  )

add_library( _polhemus SHARED "_polhemus.cpp" )

add_dependencies ( _polhemus avango_polhemus )

target_link_libraries( _polhemus
  debug ${LIBRARIES} ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} avango_polhemus
  optimized ${LIBRARIES} ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} avango_polhemus)
set_target_properties( _polhemus PROPERTIES PREFIX "")
