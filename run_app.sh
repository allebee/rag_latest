#!/bin/bash
source venv/bin/activate
export FORCE_CPU=1
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
