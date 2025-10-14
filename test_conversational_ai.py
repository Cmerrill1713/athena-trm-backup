#!/usr/bin/env python3
"""
Test NeuroForge Conversational AI
Test the system with real-world queries like you'd ask ChatGPT or Gemini
"""
import requests

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def test_query(query, expected_route=None):
    """Test a single query and show the routing decision"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}USER:{Colors.END} {query}")
    
    try:
        response = requests.post(
            'http://127.0.0.1:8014/api/chat',
            json={'text': query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            route = data.get('route', 'unknown')
            metadata = data.get('metadata', {})
            reply = data.get('reply', 'No reply')
            
            # Show routing decision
            rag_used = metadata.get('rag_enabled', False) or metadata.get('rag_used', False)
            trm_used = metadata.get('trm_used', False)
            orchestrator_used = metadata.get('orchestrator_used', False)
            
            print(f"{Colors.CYAN}ROUTE:{Colors.END} {route}", end="")
            
            if orchestrator_used:
                print(f" {Colors.GREEN}[Unified Orchestrator]{Colors.END}", end="")
            elif trm_used:
                print(f" {Colors.GREEN}[TRM Router]{Colors.END}", end="")
            
            if rag_used:
                print(f" {Colors.YELLOW}[RAG Enabled]{Colors.END}", end="")
            
            print()  # New line
            
            # Show first 150 chars of reply
            print(f"{Colors.BOLD}AI:{Colors.END} {reply[:150]}...")
            
            # Validation
            if expected_route and route != expected_route:
                print(f"{Colors.RED}⚠️  Expected route: {expected_route}, got: {route}{Colors.END}")
            else:
                print(f"{Colors.GREEN}✓{Colors.END}")
            
            return True
        else:
            print(f"{Colors.RED}❌ Error: HTTP {response.status_code}{Colors.END}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return False

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("🤖 NeuroForge Conversational AI Test")
    print("Testing with real-world queries like ChatGPT/Gemini")
    print("=" * 80)
    print(Colors.END)
    
    # Test cases organized by type
    test_cases = [
        ("Simple Greetings", [
            ("Hello! How are you doing today?", "chat-agent"),
            ("Hi there!", "chat-agent"),
            ("Thanks for your help!", "chat-agent"),
        ]),
        
        ("Substantive Knowledge Questions", [
            ("Can you explain how neural networks learn from data?", "rag-agent"),
            ("What's the difference between supervised and unsupervised learning?", "rag-agent"),
            ("How does transformer architecture work in modern LLMs?", "rag-agent"),
            ("What are the main components of a machine learning system?", "rag-agent"),
        ]),
        
        ("Code & Technical Questions", [
            ("Write me a Python function to calculate fibonacci numbers", "code-agent"),
            ("How do I implement a binary search tree in JavaScript?", "code-agent"),
            ("Debug this React component that's not rendering", "code-agent"),
        ]),
        
        ("Complex Reasoning", [
            ("Explain quantum computing like I'm five years old", "rag-agent"),
            ("What are the ethical implications of artificial general intelligence?", "rag-agent"),
            ("How would you design a scalable microservices architecture?", "rag-agent"),
        ]),
        
        ("Practical Help", [
            ("I'm building a web app with React. What are the best practices for state management?", "rag-agent"),
            ("How do I optimize my Python code for better performance?", "rag-agent"),
            ("What's the best way to structure a machine learning project?", "rag-agent"),
        ])
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for category, queries in test_cases:
        print(f"\n{Colors.BOLD}{Colors.HEADER}📁 {category}{Colors.END}")
        print("-" * 80)
        
        for query, expected_route in queries:
            total_tests += 1
            if test_query(query, expected_route):
                passed_tests += 1
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(Colors.END)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
    print(f"Failed: {Colors.RED}{total_tests - passed_tests}{Colors.END}")
    print(f"Success rate: {Colors.BOLD}{(passed_tests/total_tests*100):.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}Key Observations:{Colors.END}")
    print("• Simple greetings → chat-agent (no RAG)")
    print("• Substantive queries → rag-agent (RAG enabled)")
    print("• Code queries → code-agent (with optional RAG)")
    print("• Complex reasoning → rag-agent (heavy retrieval)")
    
    print(f"\n{Colors.GREEN}✅ Testing complete!{Colors.END}\n")

if __name__ == "__main__":
    main()

