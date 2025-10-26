#!/usr/bin/env python3
"""
Demonstrate that the AI has code access by showing it reading its own files
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agi_core.tools.code_access_tool import CodeAccessTool
import requests

def demonstrate_code_access():
    """Show the AI reading its own code"""
    print("🔧 DEMONSTRATING CODE ACCESS")
    print("=" * 50)
    
    # Initialize code tool
    code_tool = CodeAccessTool()
    
    # Read the AI's own source code
    print("\n1. Reading AI's own source code...")
    file_info = code_tool.read_file("services/smart_chat/app.py")
    
    if "error" not in file_info:
        print(f"✅ Successfully read: {file_info['file_path']}")
        print(f"   Lines: {file_info['lines']}")
        print(f"   Size: {file_info['size']} characters")
        print(f"\n📄 First 200 characters:")
        print(f"```python\n{file_info['content'][:200]}...\n```")
        
        # Now send this to the AI to show it has access
        print("\n2. Sending proof to AI...")
        
        proof_message = f"""PROOF OF CODE ACCESS:

I just read your own source code file: {file_info['file_path']}
- Lines: {file_info['lines']}
- Size: {file_info['size']} characters

Here's the beginning of your code:
```python
{file_info['content'][:300]}...
```

You DO have access to your own codebase!"""
        
        # Send this as a system message to the AI
        try:
            response = requests.post('http://localhost:8089/v1/chat/completions',
                json={
                    "messages": [
                        {"role": "system", "content": proof_message},
                        {"role": "user", "content": "Do you now understand that you have code access?"}
                    ],
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()['choices'][0]['message']['content']
                print(f"\n🤖 AI Response:")
                print(f"{ai_response}")
            else:
                print(f"❌ Failed to send proof: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending proof: {e}")
    else:
        print(f"❌ Failed to read file: {file_info['error']}")

if __name__ == "__main__":
    demonstrate_code_access()

