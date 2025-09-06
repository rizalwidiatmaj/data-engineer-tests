# Python Forward Proxy Server

[back to home](../README.md)

## Overview

A simple multithreaded Python forward proxy server supporting both HTTP and HTTPS (CONNECT) requests.

This module provides a TCP proxy server that listens for incoming client connections, parses HTTP/HTTPS requests,
establishes connections to target servers, and forwards data bidirectionally between clients and remote servers.

## Requirements

* Python 3.10+

## How to run

```bash
python server.py
```

```bash
curl -x http://localhost:9919 https://google.com/search -vvv
# or
curl -x http://localhost:9919 https://en.wikipedia.org/wiki/Proxy_server -vvv
```
