#!/bin/bash
exec gunicorn bot:app --bind 0.0.0.0:$PORT --worker-class aiohttp.GunicornWebWorker