# Integrating TRM with Your Agent Systems

This guide shows how to integrate Tiny Recursive Model (TRM) with your existing projects.

## Integration Paths

### 1. MacOS-Agent Integration

Add recursive reasoning to your MacOS automation agent.

```python
# File: MacOS-Agent/trm_reasoner.py

import torch
from typing import Dict, List
import sys
sys.path.append('/Users/christianmerrill/Documents/GitHub/TinyRecursiveModels')

from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1


class TRMReasoner:
    """Recursive reasoning for MacOS agent commands."""
    
    def __init__(self, checkpoint_path: str):
        """Initialize TRM model."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model config
        config = {
            'batch_size': 1,
            'seq_len': 512,
            'vocab_size': 50000,
            'num_puzzle_identifiers': 1000,
            'hidden_size': 512,
            'expansion': 4,
            'num_heads': 8,
            'H_cycles': 3,
            'L_cycles': 6,
            'L_layers': 2,
            'H_layers': 0,
            'pos_encodings': 'rope',
            'halt_max_steps': 16,
            'halt_exploration_prob': 0.1,
            'puzzle_emb_ndim': 512,
        }
        
        # Initialize model
        self.model = TinyRecursiveReasoningModel_ACTV1(config)
        
        # Load checkpoint
        if checkpoint_path:
            state_dict = torch.load(checkpoint_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        
        self.model.to(self.device)
        self.model.eval()
    
    def reason_about_command(self, user_query: str, context: Dict) -> Dict:
        """
        Use recursive reasoning to process user command.
        
        Args:
            user_query: User's natural language command
            context: Environmental context (files, processes, etc.)
            
        Returns:
            Dict with reasoning steps and final command
        """
        # Tokenize input
        inputs = self._prepare_input(user_query, context)
        
        # Recursive reasoning
        with torch.no_grad():
            carry = self.model.initial_carry(inputs)
            
            reasoning_steps = []
            for step in range(16):  # Max 16 refinement steps
                carry, outputs = self.model(carry, inputs)
                
                # Track reasoning
                reasoning_steps.append({
                    'step': step,
                    'halted': carry.halted.cpu().numpy(),
                    'logits': outputs['logits'].cpu(),
                })
                
                # Check if done
                if carry.halted.all():
                    break
        
        # Decode final output
        final_command = self._decode_output(outputs['logits'])
        
        return {
            'command': final_command,
            'reasoning_steps': len(reasoning_steps),
            'confidence': self._compute_confidence(outputs),
            'steps': reasoning_steps,
        }
    
    def _prepare_input(self, query: str, context: Dict) -> Dict:
        """Prepare input for TRM."""
        # Implement tokenization
        # This is a placeholder - implement based on your tokenizer
        tokens = self._tokenize(query, context)
        
        return {
            'inputs': torch.tensor([tokens], device=self.device),
            'puzzle_identifiers': torch.tensor([0], device=self.device),
        }
    
    def _decode_output(self, logits: torch.Tensor) -> str:
        """Decode TRM output to command."""
        # Implement detokenization
        # This is a placeholder
        tokens = logits.argmax(dim=-1).squeeze().cpu().numpy()
        return self._detokenize(tokens)
    
    def _compute_confidence(self, outputs: Dict) -> float:
        """Compute confidence score."""
        logits = outputs['logits']
        probs = torch.softmax(logits, dim=-1)
        max_probs = probs.max(dim=-1).values
        return max_probs.mean().item()


# Integration with existing MacOS-Agent
class EnhancedMacOSAgent:
    """MacOS Agent with TRM reasoning."""
    
    def __init__(self, checkpoint_path: str = None):
        self.reasoner = TRMReasoner(checkpoint_path) if checkpoint_path else None
        
    def process_command(self, user_query: str) -> str:
        """Process user command with recursive reasoning."""
        
        # Get system context
        context = self._get_system_context()
        
        if self.reasoner:
            # Use TRM for complex reasoning
            result = self.reasoner.reason_about_command(user_query, context)
            
            print(f"TRM used {result['reasoning_steps']} reasoning steps")
            print(f"Confidence: {result['confidence']:.2%}")
            
            return result['command']
        else:
            # Fallback to original LLM approach
            return self._llm_process(user_query, context)
    
    def _get_system_context(self) -> Dict:
        """Get current system context."""
        return {
            'cwd': os.getcwd(),
            'files': os.listdir('.'),
            'processes': [],  # Add process info
            # Add more context as needed
        }
```

### 2. PydanticAI Integration

Use TRM as a reasoning engine in PydanticAI agents.

```python
# File: pydantic-ai/examples/trm_agent.py

from pydantic_ai import Agent
from pydantic import BaseModel
import torch
import sys
sys.path.append('/Users/christianmerrill/Documents/GitHub/TinyRecursiveModels')

from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1


class TRMTool:
    """TRM as a PydanticAI tool."""
    
    def __init__(self, checkpoint_path: str):
        # Initialize TRM model
        self.model = self._load_trm(checkpoint_path)
    
    def recursive_reason(self, query: str, max_cycles: int = 16) -> str:
        """
        Apply recursive reasoning to a query.
        
        This allows the agent to iteratively refine its reasoning
        through multiple cycles, improving output quality.
        """
        # Prepare inputs
        inputs = self._tokenize(query)
        
        # Run TRM
        with torch.no_grad():
            carry = self.model.initial_carry(inputs)
            
            for _ in range(max_cycles):
                carry, outputs = self.model(carry, inputs)
                if carry.halted.all():
                    break
        
        # Return refined output
        return self._detokenize(outputs['logits'])


# Create PydanticAI agent with TRM
class CodeGenerationResult(BaseModel):
    code: str
    explanation: str
    test_cases: list[str]


trm_tool = TRMTool('/path/to/checkpoint')

agent = Agent(
    'openai:gpt-4',
    result_type=CodeGenerationResult,
    system_prompt='''You are a code generation assistant.
    Use the recursive_reason tool for complex logic.''',
)

# Register TRM as a tool
@agent.tool
def recursive_reason(query: str) -> str:
    """Use recursive reasoning for complex problems."""
    return trm_tool.recursive_reason(query)


# Use the agent
result = agent.run_sync('''
Generate a Python function to solve the N-Queens problem.
Use recursive reasoning to ensure correctness.
''')

print(result.data.code)
```

### 3. Universal AI Tools Integration

Add TRM as a reasoning backend.

```python
# File: universal-ai-tools/backends/trm_backend.py

class TRMReasoningBackend:
    """TRM reasoning backend for Universal AI Tools."""
    
    def __init__(self, config: Dict):
        self.model = self._initialize_model(config)
        self.cache = {}  # Cache for repeated queries
    
    def reason(self, 
               query: str,
               task_type: str = 'general',
               max_steps: int = 16) -> Dict:
        """
        Main reasoning endpoint.
        
        Args:
            query: Input query
            task_type: Type of reasoning task
            max_steps: Maximum reasoning steps
            
        Returns:
            Dict with results and metadata
        """
        # Check cache
        cache_key = f"{task_type}:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Run TRM
        result = self._run_trm(query, task_type, max_steps)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def batch_reason(self, queries: List[str]) -> List[Dict]:
        """Batch processing for efficiency."""
        # Implement batched inference
        pass
    
    def stream_reason(self, query: str):
        """Stream reasoning steps in real-time."""
        # Implement streaming
        pass


# Register backend
from universal_ai_tools import BackendRegistry

BackendRegistry.register('trm', TRMReasoningBackend)
```

## Fine-tuning for Your Tasks

### 1. Prepare Custom Dataset

```python
# File: TinyRecursiveModels/custom_datasets/macos_commands.py

import json
from pathlib import Path

def create_macos_command_dataset():
    """Create dataset from MacOS agent logs."""
    
    data = []
    
    # Load agent logs
    logs_dir = Path('/Users/christianmerrill/Documents/GitHub/MacOS-Agent/logs')
    for log_file in logs_dir.glob('*.json'):
        with open(log_file) as f:
            log = json.load(f)
            
            data.append({
                'input': log['user_query'],
                'output': log['generated_command'],
                'context': log['system_context'],
                'success': log['execution_success'],
            })
    
    # Convert to TRM format
    trm_data = []
    for item in data:
        if item['success']:  # Only use successful commands
            trm_data.append({
                'inputs': tokenize(item['input'] + ' ' + str(item['context'])),
                'targets': tokenize(item['output']),
            })
    
    # Save dataset
    output_path = Path('data/macos-commands')
    output_path.mkdir(exist_ok=True)
    
    torch.save(trm_data, output_path / 'train.pt')
    
    return trm_data
```

### 2. Fine-tune TRM

```bash
# Fine-tune on your custom data
python pretrain.py \
  arch=trm \
  data_paths="[data/macos-commands]" \
  epochs=10000 \
  eval_interval=1000 \
  lr=5e-5 \
  load_checkpoint=checkpoints/trm_pretrained/step_100000 \
  +run_name="trm_macos_finetuned" \
  ema=True
```

### 3. Evaluate Performance

```python
# File: experiments/evaluate_on_agent_tasks.py

def evaluate_agent_tasks():
    """Evaluate TRM on agent-specific tasks."""
    
    # Load test cases
    test_cases = load_macos_test_cases()
    
    # Initialize models
    trm_model = load_trm_model('checkpoints/trm_macos_finetuned/step_10000')
    baseline_model = load_baseline()  # Your current LLM
    
    # Compare
    trm_results = []
    baseline_results = []
    
    for test in test_cases:
        # TRM
        trm_output = trm_model.reason(test['input'])
        trm_results.append({
            'success': evaluate_command(trm_output, test['expected']),
            'latency': trm_output['latency'],
            'steps': trm_output['reasoning_steps'],
        })
        
        # Baseline
        baseline_output = baseline_model.generate(test['input'])
        baseline_results.append({
            'success': evaluate_command(baseline_output, test['expected']),
            'latency': baseline_output['latency'],
        })
    
    # Report
    print(f"TRM Success Rate: {sum(r['success'] for r in trm_results) / len(trm_results):.2%}")
    print(f"Baseline Success Rate: {sum(r['success'] for r in baseline_results) / len(baseline_results):.2%}")
    print(f"TRM Avg Latency: {sum(r['latency'] for r in trm_results) / len(trm_results):.3f}s")
    print(f"Baseline Avg Latency: {sum(r['latency'] for r in baseline_results) / len(baseline_results):.3f}s")
```

## Deployment Options

### Option 1: Local Deployment (Recommended for MacOS-Agent)

```bash
# Quantize model for faster inference
python -m scripts.quantize_model \
  --checkpoint checkpoints/trm_macos_finetuned/step_10000 \
  --output models/trm_macos_int8.pt \
  --precision int8

# Package with agent
cp models/trm_macos_int8.pt MacOS-Agent/models/
```

### Option 2: API Deployment

```python
# File: TinyRecursiveModels/api/serve.py

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Load model
model = load_trm_model()

class ReasoningRequest(BaseModel):
    query: str
    max_steps: int = 16

class ReasoningResponse(BaseModel):
    result: str
    steps: int
    confidence: float
    latency_ms: float

@app.post("/reason", response_model=ReasoningResponse)
async def reason(request: ReasoningRequest):
    """Reasoning endpoint."""
    import time
    start = time.time()
    
    result = model.reason(request.query, max_steps=request.max_steps)
    
    return ReasoningResponse(
        result=result['output'],
        steps=result['steps'],
        confidence=result['confidence'],
        latency_ms=(time.time() - start) * 1000,
    )

# Run: uvicorn api.serve:app --host 0.0.0.0 --port 8000
```

### Option 3: Edge Deployment (iOS/Swift)

For your SwiftUI projects:

```swift
// File: Models/TRMReasoning.swift

import CoreML

class TRMReasoner {
    private var model: MLModel
    
    init() {
        // Load converted CoreML model
        guard let modelURL = Bundle.main.url(forResource: "TRM", withExtension: "mlmodelc"),
              let model = try? MLModel(contentsOf: modelURL) else {
            fatalError("Failed to load TRM model")
        }
        self.model = model
    }
    
    func reason(query: String, maxSteps: Int = 16) -> ReasoningResult {
        // Tokenize input
        let tokens = tokenize(query)
        
        // Run inference
        // ... CoreML inference code ...
        
        return ReasoningResult(
            output: output,
            steps: steps,
            confidence: confidence
        )
    }
}
```

## Performance Optimization

### 1. Model Quantization

```python
# Quantize to INT8 (2x smaller, minimal accuracy loss)
import torch.quantization as quantization

model_int8 = quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

# Quantize to INT4 (4x smaller)
# Requires custom implementation or GPTQ/AWQ
```

### 2. Batch Processing

```python
# Process multiple queries in parallel
def batch_reason(queries: List[str], model: TRM) -> List[str]:
    # Tokenize all
    inputs = [tokenize(q) for q in queries]
    
    # Pad to same length
    max_len = max(len(inp) for inp in inputs)
    padded = [pad(inp, max_len) for inp in inputs]
    
    # Batch inference
    batch = torch.stack(padded)
    outputs = model(batch)
    
    # Decode all
    return [decode(out) for out in outputs]
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_reason(query: str) -> str:
    return model.reason(query)
```

## Next Steps

1. **Choose integration path** (MacOS-Agent recommended to start)
2. **Collect training data** from your agent logs
3. **Fine-tune TRM** on your specific tasks
4. **Evaluate** against your current system
5. **Deploy** and monitor performance

Need help with any step? Let me know!

