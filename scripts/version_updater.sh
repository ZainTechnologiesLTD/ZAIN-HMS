# Automated Version Update Script
# This script updates the version throughout the codebase

#!/bin/bash

VERSION_FILE="zain_hms/version.py"
SETTINGS_FILES=("zain_hms/settings.py" "zain_hms/production_settings.py" "update_system_settings.py")
DOCKER_FILES=("docker/Dockerfile.prod" "docker-compose.prod.yml")

# Function to update version in all relevant files
update_version_everywhere() {
    local new_version=$1
    
    echo "🔄 Updating version to $new_version in all files..."
    
    # Update Django settings files
    for file in "${SETTINGS_FILES[@]}"; do
        if [ -f "$file" ]; then
            sed -i.bak "s/VERSION = .*/VERSION = '$new_version'/" "$file"
            echo "   ✅ Updated $file"
        fi
    done
    
    # Update package.json if exists
    if [ -f "package.json" ]; then
        sed -i.bak "s/\"version\": \".*\"/\"version\": \"$new_version\"/" package.json
        echo "   ✅ Updated package.json"
    fi
    
    # Update Docker files
    for file in "${DOCKER_FILES[@]}"; do
        if [ -f "$file" ]; then
            sed -i.bak "s/VERSION=.*/VERSION=$new_version/" "$file"
            echo "   ✅ Updated $file"
        fi
    done
    
    # Clean up backup files
    find . -name "*.bak" -delete
    
    echo "✅ Version updated to $new_version in all files"
}

# Export the function for use in other scripts
export -f update_version_everywhere