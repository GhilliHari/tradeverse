#!/bin/bash

echo "🚀 Tradeverse GitHub Push Helper"
echo "=================================="
echo ""
echo "This script will help you push your code to GitHub."
echo ""
echo "You'll need a GitHub Personal Access Token (PAT)."
echo ""
echo "📝 To create a token (takes 1 minute):"
echo "   1. Go to: https://github.com/settings/tokens/new"
echo "   2. Note: 'Tradeverse Deploy'"
echo "   3. Expiration: 90 days"
echo "   4. Check: ✅ repo (full control of private repositories)"
echo "   5. Click 'Generate token'"
echo "   6. COPY the token (you won't see it again!)"
echo ""
echo "Press Enter when you have your token ready..."
read -r

echo ""
read -sp "Paste your GitHub token here (it won't be shown): " token
echo ""

if [ -z "$token" ]; then
    echo "❌ Token cannot be empty!"
    exit 1
fi

echo ""
echo "📡 Pushing to GitHub..."
echo ""

# Change remote to use username:token so Git never prompts interactively for a password
git remote set-url origin "https://GhilliHari:$token@github.com/GhilliHari/tradeverse.git"

# Ensure all backup manifests & data are staged
if [ -x "./backend/.venv/bin/python3" ]; then
    ./backend/.venv/bin/python3 ./backend/run_market_simulation.py --days 14
fi
git add -f backend/data/ backend/observatory_data/ backend/knowledge_base/ || true
git diff --staged --quiet || git commit -m "chore(backup): sync all Tradeverse backup data to GitHub"

# Push
GIT_TERMINAL_PROMPT=0 git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Your code and all backup data are now on GitHub!"
    echo "   https://github.com/GhilliHari/tradeverse"
    echo ""
    echo "🎯 Automatic GitHub backup sync is now active!"
else
    echo ""
    echo "❌ Push failed. Please check the error above."
    exit 1
fi
