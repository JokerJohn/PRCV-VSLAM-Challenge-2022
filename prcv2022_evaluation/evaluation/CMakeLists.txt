cmake_minimum_required(VERSION 3.3.2)
project(ramlab_evaluation)

# explicitly set std=c++14 to remove errors from pcl library
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -O3")
set(CMAKE_CXX_FLAGS "-O3")

find_package(catkin_simple REQUIRED)
catkin_simple(ALL_DEPS_REQUIRED)

# find_package(OpenCV REQUIRED)
# find_package(yaml-cpp REQUIRED)

include_directories(include ${catkin_INCLUDE_DIRS})

################################ library
# set(HEADERS 
#)

# set(SOURCES 
#)

# cs_add_library(${PROJECT_NAME} ${HEADERS} ${SOURCES} yaml-cpp)

################################ executable
cs_add_executable(cpurelative src/cpurelative.cpp)
target_link_libraries(cpurelative)

cs_install()
cs_export()