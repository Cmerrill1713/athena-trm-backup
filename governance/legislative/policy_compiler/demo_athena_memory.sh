#!/bin/bash

# ATHENA PERSISTENT MEMORY DEMO
# Demonstrates learning and memory capabilities

echo "🧠 ATHENA PERSISTENT MEMORY DEMO"
echo "================================="
echo ""

# Check if Athena memory system is available
if [ ! -f "/opt/ai-republic/athena_memory_system.py" ]; then
    echo "❌ Athena memory system not found. Please install Athena first:"
    echo "   sudo ./install_athena_copilot.sh"
    exit 1
fi

echo "✅ Athena memory system detected"
echo ""

# Demo 1: Memory System Initialization
echo "🧠 DEMO 1: Memory System Status"
echo "-------------------------------"
python3 -c "
from athena_memory_system import get_memory_system
memory = get_memory_system()
stats = memory.get_memory_stats()
print('Current Memory Status:')
for key, value in stats.items():
    print(f'  • {key}: {value}')
"
echo ""

# Demo 2: Learning from Interactions
echo "🎓 DEMO 2: Learning from Interactions"
echo "-------------------------------------"
echo "Athena learns patterns from your usage:"
echo ""

# Simulate some interactions
python3 -c "
from athena_memory_system import learn_from_interaction

# Simulate learning from multiple interactions
learn_from_interaction('check system status', 'status_check', True, 'All systems operational')
learn_from_interaction('show me the logs', 'show_logs', True, 'Recent activity displayed')
learn_from_interaction('what are the metrics?', 'show_metrics', True, 'Metrics shown')
learn_from_interaction('check tribunals', 'check_tribunals', True, 'No tribunals active')
learn_from_interaction('show me the logs', 'show_logs', True, 'Recent activity displayed')  # Repeat
learn_from_interaction('check system status', 'status_check', True, 'All systems operational')  # Repeat

print('✅ Learned from 6 interactions')
print('   • Command frequencies tracked')
print('   • Success patterns recorded')
print('   • User preferences learned')
"

echo ""

# Demo 3: Personalized Suggestions
echo "💡 DEMO 3: Personalized Suggestions"
echo "-----------------------------------"
python3 -c "
from athena_memory_system import get_memory_system, get_personalized_suggestions

memory = get_memory_system()
suggestions = get_personalized_suggestions('check')

print('Based on your usage patterns, when you say \"check\":')
if suggestions:
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f'  {i}. \"{suggestion}\"')
else:
    print('  (No suggestions yet - need more interactions)')
"
echo ""

# Demo 4: User Favorites
echo "⭐ DEMO 4: Learning User Favorites"
echo "----------------------------------"
python3 -c "
from athena_memory_system import get_memory_system

memory = get_memory_system()
favorites = memory.get_user_favorites()

print('Your most frequently used commands:')
if favorites:
    for i, cmd in enumerate(favorites[:5], 1):
        print(f'  {i}. \"{cmd}\"')
else:
    print('  (No favorites yet - need more interactions)')
"
echo ""

# Demo 5: Context Transitions
echo "🔄 DEMO 5: Context Learning"
echo "---------------------------"
echo "Athena learns what you typically do after certain actions:"
echo ""
python3 -c "
from athena_memory_system import get_memory_system

memory = get_memory_system()

# Show some learned transitions
transitions = memory.long_term_memory.get('context_transitions', {})
if transitions:
    print('Learned command transitions:')
    for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f'  \"{transition}\" (occurred {count} times)')
else:
    print('  (No transitions learned yet - need more interactions)')
"
echo ""

# Demo 6: Memory Persistence
echo "💾 DEMO 6: Memory Persistence"
echo "-----------------------------"
echo "Memory persists across sessions and reboots:"
echo ""

# Check if memory files exist
memory_dir="/var/lib/ai-republic/athena_memory"
if [ -d "$memory_dir" ]; then
    echo "✅ Memory directory exists: $memory_dir"
    echo "Files present:"
    ls -la "$memory_dir" 2>/dev/null | grep -E "\.(json|gz)$" | while read line; do
        echo "  $line"
    done

    # Count conversation archives
    conv_count=$(find "$memory_dir/conversations" -name "*.gz" 2>/dev/null | wc -l)
    echo "  Conversation archives: $conv_count files"
else
    echo "❌ Memory directory not created yet (will be created on first use)"
fi

echo ""

# Demo 7: Future Capabilities
echo "🚀 DEMO 7: Future Learning Capabilities"
echo "---------------------------------------"
echo "Athena will continue learning:"
echo ""
echo "• Command completion suggestions"
echo "• Predictive next actions"
echo "• Preferred response styles"
echo "• Frequently accessed information"
echo "• Custom command shortcuts"
echo "• Usage pattern optimization"
echo ""

echo "🎯 MEMORY SYSTEM SUMMARY:"
echo "• Persistent learning across sessions and reboots"
echo "• Pattern recognition from usage history"
echo "• Personalized suggestions and predictions"
echo "• Context-aware conversation flow"
echo "• Optimized memory management and cleanup"
echo "• Complete audit trail of learned behaviors"
echo ""

echo "🚀 ACTIVATION:"
echo "1. Persistent memory is now active in all Athena conversations"
echo "2. Try: athena-chat (converse and watch Athena learn)"
echo "3. After a few interactions, ask: 'what do you remember?'"
echo "4. Check memory stats: 'memory stats'"
echo ""

echo "📖 For full documentation:"
echo "   athena_memory_system.py - Memory implementation"
echo "   ATHENA_CONVERSATIONAL_GUIDE.md - Usage guide"
echo ""

echo "🧠 Athena Persistent Memory Demo Complete!"
echo "Athena now learns and remembers across all sessions! 🎓🤖💾"
