# 🔄 Development to Main Branch Workflow

## 📋 **Current Branch Status**

All branches are currently synced. Here's the proper workflow for future changes:

## 🚀 **Step-by-Step Workflow**

### **1. Making New Changes (Development First)**

```bash
# Start from development branch
git checkout development

# Create feature branch for new work
git checkout -b feature/your-new-feature

# Make your changes to files
# Edit install.sh, docker-compose.prod.yml, etc.

# Commit your changes
git add .
git commit -m "feat: your new feature description"

# Push feature branch
git push origin feature/your-new-feature
```

### **2. Merge Feature to Development**

```bash
# Switch to development
git checkout development

# Merge your feature
git merge feature/your-new-feature

# Push development with new changes
git push origin development
```

### **3. When Ready: Development → Main**

```bash
# Switch to main branch
git checkout main

# Merge development into main
git merge development

# Push main branch (production deployment)
git push origin main
```

## ⚡ **Automated Workflow Scripts**

### **Script 1: Quick Development Push**
```bash
#!/bin/bash
# File: scripts/push-to-development.sh

echo "🔄 Pushing changes to development branch..."

# Ensure we're on development branch
git checkout development

# Add all changes
git add .

# Commit with timestamp
read -p "Enter commit message: " message
git commit -m "$message"

# Push to development
git push origin development

echo "✅ Changes pushed to development branch!"
echo "📝 To deploy to production, run: ./scripts/deploy-to-main.sh"
```

### **Script 2: Development → Main Deployment**
```bash
#!/bin/bash
# File: scripts/deploy-to-main.sh

echo "🚀 Deploying development to main (production)..."

# Switch to main
git checkout main

# Check if development has new commits
BEHIND=$(git rev-list --count main..development)

if [ "$BEHIND" -eq 0 ]; then
    echo "✅ Main is already up to date with development"
    exit 0
fi

echo "📦 Development is $BEHIND commits ahead of main"
echo "🔄 Merging development → main..."

# Merge development
git merge development

# Push to production
git push origin main

echo "✅ Successfully deployed to production (main branch)!"
echo "🌐 Live at: https://github.com/ZainTechnologiesLTD/ZAIN-HMS"
```

## 🔧 **GitHub Actions Auto-Deployment**

### **Automatic Main Deployment on Development Push**

Create `.github/workflows/auto-deploy.yml`:

```yaml
name: Auto Deploy Development to Main

on:
  push:
    branches: [ development ]
  workflow_dispatch: # Manual trigger

jobs:
  auto-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
        token: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Configure Git
      run: |
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
    
    - name: Check if main needs update
      id: check
      run: |
        git checkout main
        BEHIND=$(git rev-list --count main..development)
        echo "commits_behind=$BEHIND" >> $GITHUB_OUTPUT
        echo "Main is $BEHIND commits behind development"
    
    - name: Deploy to Main
      if: steps.check.outputs.commits_behind != '0'
      run: |
        echo "🚀 Auto-deploying development to main..."
        git merge development
        git push origin main
        echo "✅ Successfully auto-deployed to main!"
    
    - name: Create Release
      if: steps.check.outputs.commits_behind != '0'
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: auto-v${{ github.run_number }}
        release_name: Auto Release v${{ github.run_number }}
        body: |
          🚀 Automatic deployment from development branch
          
          Changes included in this release:
          ${{ github.event.head_commit.message }}
        draft: false
        prerelease: false
```

## 📊 **Branch Management Commands**

### **Check Branch Status**
```bash
# See all branches and their status
git branch -a

# See commits differences
git log main..development --oneline

# See file differences
git diff main development
```

### **Quick Commands**
```bash
# Update development with your changes
git checkout development
git add .
git commit -m "your message"
git push origin development

# Deploy development to main
git checkout main
git merge development
git push origin main
```

## 🎯 **Best Practices**

### **1. Always Development First**
- ✅ Make changes in development branch
- ✅ Test in development environment
- ✅ Then merge to main for production

### **2. Feature Branches for Major Changes**
- ✅ Create `feature/feature-name` branches
- ✅ Merge to development first
- ✅ Then development to main

### **3. Main Branch Protection**
- ✅ Main should only receive tested code from development
- ✅ Direct commits to main should be rare
- ✅ Use development as staging environment

## 🔄 **Current Workflow Summary**

```
Your Changes
    ↓
Development Branch (testing/staging)
    ↓ (when ready)
Main Branch (production/live)
    ↓
GitHub Releases & Deployments
```

## 📝 **Next Steps for You**

1. **For new changes**: Always start in `development` branch
2. **Test thoroughly**: In development environment
3. **Deploy to production**: Merge development → main
4. **Use the scripts**: I'll create automation scripts for you

This ensures your production (main) branch is always stable! 🚀