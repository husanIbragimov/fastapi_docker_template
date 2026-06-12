#!/bin/sh
set -e
exec arq app.background.worker.WorkerSettings
