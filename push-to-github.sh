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

# Change remote to use token
git remote set-url origin "https://$token@github.com/GhilliHari/tradeverse.git"

# Push
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Your code is now on GitHub!"
    echo "   https://github.com/GhilliHari/tradeverse"
    echo ""
    echo "🎯 Next: Deploy to Render!"
    
    # Reset remote to not include token
    git remote set-url origin "https://github.com/GhilliHari/tradeverse.git"
else
    echo ""
    echo "❌ Push failed. Please check the error above."
    exit 1
fi
