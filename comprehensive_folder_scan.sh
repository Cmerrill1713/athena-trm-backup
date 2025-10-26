#!/bin/bash
# Comprehensive scan of all 47 root folders for family features

echo "🔍 COMPREHENSIVE FOLDER SCAN FOR FAMILY FEATURES"
echo "================================================"
echo ""

# Get all root folders
folders=$(ls -d */ 2>/dev/null | grep -v node_modules)

for folder in $folders; do
    echo "📁 $folder"
    
    # Count Python files
    py_count=$(find "$folder" -name "*.py" -type f 2>/dev/null | wc -l | tr -d ' ')
    
    # Check for specific features
    has_calendar=$(find "$folder" -name "*.py" -type f -exec grep -l "calendar\|schedule" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_todo=$(find "$folder" -name "*.py" -type f -exec grep -l "todo\|task.*list" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_education=$(find "$folder" -name "*.py" -type f -exec grep -l "homework\|education\|quiz" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_health=$(find "$folder" -name "*.py" -type f -exec grep -l "health\|medication\|wellness" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_meal=$(find "$folder" -name "*.py" -type f -exec grep -l "meal\|recipe\|food\|grocery" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_financial=$(find "$folder" -name "*.py" -type f -exec grep -l "budget\|expense\|financial" {} \; 2>/dev/null | wc -l | tr -d ' ')
    has_safety=$(find "$folder" -name "*.py" -type f -exec grep -l "safety\|kid\|child\|parent" {} \; 2>/dev/null | wc -l | tr -d ' ')
    
    # Show if any features found
    if [ "$has_calendar" -gt 0 ] || [ "$has_todo" -gt 0 ] || [ "$has_education" -gt 0 ] || [ "$has_health" -gt 0 ] || [ "$has_meal" -gt 0 ] || [ "$has_financial" -gt 0 ] || [ "$has_safety" -gt 0 ]; then
        echo "  📊 Python files: $py_count"
        [ "$has_calendar" -gt 0 ] && echo "  📅 Calendar/Schedule: $has_calendar files"
        [ "$has_todo" -gt 0 ] && echo "  ✅ Todo/Tasks: $has_todo files"
        [ "$has_education" -gt 0 ] && echo "  📚 Education: $has_education files"
        [ "$has_health" -gt 0 ] && echo "  🏥 Health: $has_health files"
        [ "$has_meal" -gt 0 ] && echo "  🍽️  Meals: $has_meal files"
        [ "$has_financial" -gt 0 ] && echo "  💰 Financial: $has_financial files"
        [ "$has_safety" -gt 0 ] && echo "  🛡️  Safety: $has_safety files"
        echo ""
    fi
done

echo "✅ Scan complete!"
