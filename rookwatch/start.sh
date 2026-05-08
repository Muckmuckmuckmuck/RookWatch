#!/bin/bash
clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   WORKVERIFY — VIDEO ANALYSIS MVP        ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

if ! command -v python3 &>/dev/null; then
  echo "  ✗ Python3 not found. Install from python.org/downloads"
  exit 1
fi

echo "  Installing dependencies (silent)…"
pip3 install -r requirements.txt -q
echo "  ✓ Ready"
echo ""

if [ -z "$GOOGLE_API_KEY" ]; then
  echo "  ⚠  Warning: GOOGLE_API_KEY env var not set."
  echo "     Either set it: export GOOGLE_API_KEY='AIza...'"
  echo "     Or paste it directly in server.py"
  echo ""
fi

echo "  ┌──────────────────────────────────────────┐"
echo "  │  💻 Recording Page                       │"
echo "  │     http://localhost:5000                │"
echo "  │                                          │"
echo "  │  📊 Full Report                          │"
echo "  │     http://localhost:5000/report         │"
echo "  └──────────────────────────────────────────┘"
echo ""

python3 server.py
