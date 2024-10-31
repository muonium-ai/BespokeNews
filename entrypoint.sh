#!/bin/bash
# Start the background worker
python concurrent_cron.py &

# Start the Flask application
flask run --host=0.0.0.0