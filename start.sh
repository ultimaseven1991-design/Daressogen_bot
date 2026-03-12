#!/bin/bash
gunicorn Daressogen_bot:app --bind 0.0.0.0:$PORT
