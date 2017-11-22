cmake_minimum_required(VERSION 2.8)

project(filler)

set(PROJECT_SOURCES
  list.h
  util.h
  util.c
  filler.c
)

add_executable(filler ${PROJECT_SOURCES})
set_target_properties(filler PROPERTIES
  C_STANDARD 99
)
