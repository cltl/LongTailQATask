#!/bin/bash
    curl -s -I "https://web.archive.org/save/$1" |
    grep Content-Location |
    awk '{printf( "https://web.archive.org/%s\n",$2)}';
