#!/usr/bin/env python3
"""
Debug tokenization to find the tensor creation issue
"""

import json
from transformers import AutoTokenizer
from datasets import Dataset

# Load data
with open('training/processed_data/train_dataset_20250822_150258.json', 'r') as f:
    data = json.load(f)

training_data = data[:23]
print(f"✅ Loaded {len(training_data)} examples")

# Load tokenizer
model_name = "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Create dataset
dataset = Dataset.from_list(training_data)
print("Dataset created successfully")
print("Dataset features:", dataset.features)
print("First example:", dataset[0])

# Test tokenization function
def tokenize_function(examples):
    print("🔍 Input to tokenize_function:")
    print("Type of examples:", type(examples))
    print("Keys in examples:", examples.keys())
    print("Type of examples['text']:", type(examples['text']))
    
    if isinstance(examples['text'], list):
        print("✅ text is a list with length:", len(examples['text']))
        print("First text preview:", repr(examples['text'][0][:100]))
    else:
        print("❌ text is NOT a list:", type(examples['text']))
        print("Text preview:", repr(examples['text'][:100]))
    
    try:
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors=None
        )
        print("✅ Tokenization successful")
        print("Tokenized keys:", tokenized.keys())
        print("input_ids type:", type(tokenized["input_ids"]))
        
        # Add labels
        tokenized["labels"] = tokenized["input_ids"].copy()
        print("✅ Labels added")
        return tokenized
        
    except Exception as e:
        print(f"❌ Tokenization failed: {e}")
        raise e

# Test with single example
print("\n=== Testing single example ===")
single_example = {"text": training_data[0]["text"]}
try:
    result = tokenize_function(single_example)
    print("Single example tokenization: SUCCESS")
except Exception as e:
    print(f"Single example tokenization FAILED: {e}")

# Test with batched examples
print("\n=== Testing batched mapping ===")
try:
    tokenized_dataset = dataset.map(tokenize_function, batched=True, batch_size=2)
    print("Batched mapping: SUCCESS")
    print("Tokenized dataset:", tokenized_dataset)
except Exception as e:
    print(f"Batched mapping FAILED: {e}")