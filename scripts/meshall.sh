#!/bin/bash
  for f in *.stl; do
    [ -f "$f" ] && admesh "$f" -b "$f"
  done