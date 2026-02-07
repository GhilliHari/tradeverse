#!/bin/bash

# Tradeverse GitHub Setup Script
# Run this after creating your GitHub repository

echo "🚀 Setting up GitHub remote for Tradeverse..."
echo ""
echo "⚠️  IMPORTANT: Replace YOUR_USERNAME with your actual GitHub username"
echo ""
echo "Example: If your username is 'john', use:"
echo "  git remote add origin https://github.com/john/tradeverse.git"
echo ""
read -p "Enter your GitHub username: " username

if [ -z "$username" ]; then
    echo "❌ Username cannot be empty!"
    exit 1
fi

echo ""
echo "📡 Adding remote origin..."
git remote add origin "https://github.com/$username/tradeverse.git"

echo "🌿 Setting main branch..."
git branch -M main

echo "⬆️  Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Your code is now on GitHub at:"
echo "   https://github.com/$username/tradeverse"
echo ""
echo "🎯 Next step: Deploy to Render!"
