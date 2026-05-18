#!/bin/bash
clear
echo ""
echo "  =========================================="
echo "    ROOKWATCH - AI WORK VERIFICATION MVP"
echo "  =========================================="
echo ""

if ! command -v python3 &>/dev/null; then
  echo "  X  Python3 not found. Install from python.org/downloads"
  exit 1
fi

echo "  Installing dependencies (silent)..."
pip3 install -r requirements.txt -q
echo "  Ready."
echo ""

if [ -z "$GOOGLE_API_KEY" ]; then
  echo "  Warning: GOOGLE_API_KEY env var not set."
  echo "    Set it: export GOOGLE_API_KEY='AIza...'"
  echo ""
fi

echo "  --------------------------------------------"
echo "    Pitch site   http://localhost:5000/"
echo "    Recording    http://localhost:5000/demo"
echo "    Report       http://localhost:5000/report"
echo "  --------------------------------------------"
echo ""

python3 server.py
