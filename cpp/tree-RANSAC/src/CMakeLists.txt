find_package(Corrade REQUIRED Main)
find_package(Magnum REQUIRED GL Sdl2Application SceneGraph)
find_package(CGAL)

set_directory_properties(PROPERTIES CORRADE_USE_PEDANTIC_FLAGS ON)

add_definitions(
  -DJSON_PARAMS_PATH=\"${PROJECT_SOURCE_DIR}/../../_data/trees/params.json\"
)

corrade_add_resource(PointShader_RESOURCES Viewer/resources.conf)
add_executable(hw03 
  main.cpp
  TreeDetector.cpp
  Viewer/Viewer.cpp
  Viewer/PointShader.cpp
  Viewer/ArcBall.cpp
  ${PointShader_RESOURCES}
)
target_link_libraries(hw03 PRIVATE
  CGAL::CGAL
  Corrade::Main
  Magnum::Application
  Magnum::GL
  Magnum::Magnum
  Magnum::SceneGraph
  MagnumIntegration::ImGui
)
set_target_properties(hw03 PROPERTIES 
  CXX_STANDARD 17
)

# Make the executable a default target to build & run in Visual Studio
set_property(DIRECTORY ${PROJECT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT hw03)
