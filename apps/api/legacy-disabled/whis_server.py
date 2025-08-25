#!/usr/bin/env python3
"""
🚀 WHIS API Server
==================
One-command API startup with automatic adapter and RAG index loading.
The "dream setup" serving layer.

Features:
- Automatic model + adapter loading from registry
- RAG integration with vector search
- Health probes and metrics
- Hot-swappable adapters
- Rate limiting and security
"""

import os
import json
import yaml
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

from registry.model_registry import WhisModelRegistry
from rag.embed import WhisRAGPipeline


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    max_tokens: int = 500
    temperature: float = 0.7


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Dict]] = None
    model_info: Dict[str, str]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    rag_available: bool
    current_adapter: Optional[str]
    uptime_seconds: float
    version: str


class WhisAPIServer:
    """WHIS API Server with automatic model loading"""
    
    def __init__(self, config_path: str = "ai-training/serve/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.registry = WhisModelRegistry()
        
        # Model components
        self.tokenizer = None
        self.model = None
        self.current_adapter = None
        self.rag_pipeline = None
        
        # Server state
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        
        # Create FastAPI app
        self.app = self._create_app()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load serving configuration"""
        if not self.config_path.exists():
            # Create default config
            default_config = {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": False
                },
                "model": {
                    "base_model_path": "models/whis-base",
                    "auto_load_adapter": "production",  # Load production adapter
                    "device": "auto",
                    "torch_dtype": "bfloat16"
                },
                "rag": {
                    "enabled": True,
                    "config_path": "ai-training/configs/rag.yaml",
                    "auto_initialize": True
                },
                "security": {
                    "require_auth": False,
                    "api_key": "${WHIS_API_KEY}",
                    "rate_limit_requests": 60,
                    "rate_limit_window": 60
                },
                "monitoring": {
                    "enable_metrics": True,
                    "log_requests": True,
                    "health_check_interval": 30
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, indent=2)
                
            return default_config
            
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="WHIS SOAR-Copilot API",
            description="AI-powered SOAR copilot with RAG capabilities",
            version="1.0.0"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Security
        security = HTTPBearer() if self.config["security"]["require_auth"] else None
        
        @app.middleware("http")
        async def track_requests(request: Request, call_next):
            self.request_count += 1
            start_time = datetime.now()
            
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                self.error_count += 1
                raise
                
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return HealthResponse(
                status="healthy" if self.model is not None else "loading",
                model_loaded=self.model is not None,
                rag_available=self.rag_pipeline is not None,
                current_adapter=self.current_adapter,
                uptime_seconds=uptime,
                version="1.0.0"
            )
            
        @app.post("/chat", response_model=ChatResponse)
        async def chat(
            request: ChatRequest,
            credentials: Optional[HTTPAuthorizationCredentials] = Security(security) if security else None
        ):
            """Main chat endpoint"""
            if not self.model or not self.tokenizer:
                raise HTTPException(status_code=503, detail="Model not loaded")
                
            try:
                # Generate response
                if request.use_rag and self.rag_pipeline:
                    response, sources = await self._generate_rag_response(
                        request.message, 
                        request.max_tokens,
                        request.temperature
                    )
                else:
                    response = await self._generate_direct_response(
                        request.message,
                        request.max_tokens, 
                        request.temperature
                    )
                    sources = None
                    
                return ChatResponse(
                    response=response,
                    sources=sources,
                    model_info={
                        "adapter": self.current_adapter or "base",
                        "rag_enabled": str(request.use_rag and self.rag_pipeline is not None)
                    },
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                self.error_count += 1
                raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")
                
        @app.post("/reload-adapter")
        async def reload_adapter(adapter_reference: Optional[str] = None):
            """Hot-reload adapter"""
            try:
                if adapter_reference:
                    success = await self._load_adapter(adapter_reference)
                else:
                    # Reload current production adapter
                    success = await self._load_production_adapter()
                    
                if success:
                    return {"status": "success", "adapter": self.current_adapter}
                else:
                    raise HTTPException(status_code=400, detail="Failed to load adapter")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Reload error: {str(e)}")
                
        @app.get("/metrics")
        async def get_metrics():
            """Get server metrics"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "model_info": {
                    "loaded": self.model is not None,
                    "adapter": self.current_adapter,
                    "rag_enabled": self.rag_pipeline is not None
                }
            }
            
        return app
        
    async def _load_base_model(self) -> bool:
        """Load base model and tokenizer"""
        try:
            model_config = self.config["model"]
            base_path = model_config["base_model_path"]
            
            print(f"🔧 Loading base model: {base_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_path,
                trust_remote_code=True
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            # Load model
            torch_dtype = getattr(torch, model_config["torch_dtype"])
            self.model = AutoModelForCausalLM.from_pretrained(
                base_path,
                torch_dtype=torch_dtype,
                device_map=model_config["device"],
                trust_remote_code=True
            )
            
            print("✅ Base model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load base model: {e}")
            return False
            
    async def _load_adapter(self, adapter_reference: str) -> bool:
        """Load specific adapter"""
        try:
            if adapter_reference not in self.registry.metadata["adapters"]:
                print(f"❌ Adapter not found: {adapter_reference}")
                return False
                
            adapter_info = self.registry.metadata["adapters"][adapter_reference]
            adapter_path = adapter_info["registry_path"]
            
            print(f"🔧 Loading adapter: {adapter_reference}")
            
            # Load adapter onto base model
            if self.model:
                self.model = PeftModel.from_pretrained(self.model, adapter_path)
                self.current_adapter = adapter_reference
                print(f"✅ Adapter loaded: {adapter_reference}")
                return True
            else:
                print("❌ Base model not loaded")
                return False
                
        except Exception as e:
            print(f"❌ Failed to load adapter {adapter_reference}: {e}")
            return False
            
    async def _load_production_adapter(self) -> bool:
        """Load current production adapter"""
        prod_deployment = self.registry.get_current_deployment("production")
        if prod_deployment:
            return await self._load_adapter(prod_deployment["adapter"])
        else:
            print("⚠️ No production adapter deployed")
            return True  # Not an error, just no adapter
            
    async def _initialize_rag(self) -> bool:
        """Initialize RAG pipeline"""
        try:
            if not self.config["rag"]["enabled"]:
                return True
                
            rag_config_path = self.config["rag"]["config_path"]
            
            print("🔧 Initializing RAG pipeline...")
            self.rag_pipeline = WhisRAGPipeline(rag_config_path)
            
            if self.config["rag"]["auto_initialize"]:
                self.rag_pipeline.initialize()
                
            print("✅ RAG pipeline initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize RAG: {e}")
            return False
            
    async def _generate_direct_response(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate direct response without RAG"""
        formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if "<|im_start|>assistant\n" in response:
            response = response.split("<|im_start|>assistant\n")[-1].strip()
            
        return response
        
    async def _generate_rag_response(self, query: str, max_tokens: int, temperature: float) -> tuple:
        """Generate RAG-enhanced response"""
        # Retrieve relevant context
        retrieved = self.rag_pipeline.query(query, top_k=5)
        
        # Build context
        context_pieces = []
        sources = []
        
        for item in retrieved:
            context_pieces.append(item["text"])
            sources.append({
                "text": item["text"][:200] + "..." if len(item["text"]) > 200 else item["text"],
                "source": item["metadata"].get("source", "unknown"),
                "distance": item.get("distance", 0)
            })
            
        context_str = "\n\n".join(context_pieces)
        
        # Build RAG prompt
        rag_prompt = f"""Context:
{context_str}

User Question: {query}

Based on the provided context, please provide a helpful and accurate response. If the context doesn't contain relevant information, please say so."""
        
        # Generate response
        response = await self._generate_direct_response(rag_prompt, max_tokens, temperature)
        
        return response, sources
        
    async def initialize(self) -> bool:
        """Initialize all server components"""
        print("🚀 Initializing WHIS API Server...")
        
        # Load base model
        if not await self._load_base_model():
            return False
            
        # Load adapter if configured
        auto_load = self.config["model"]["auto_load_adapter"]
        if auto_load == "production":
            await self._load_production_adapter()
        elif auto_load and auto_load != "none":
            await self._load_adapter(auto_load)
            
        # Initialize RAG
        if not await self._initialize_rag():
            print("⚠️ RAG initialization failed, continuing without RAG")
            
        print("✅ WHIS API Server initialized successfully")
        return True
        
    def run(self):
        """Run the API server"""
        server_config = self.config["server"]
        uvicorn.run(
            self.app,
            host=server_config["host"],
            port=server_config["port"],
            reload=server_config["reload"]
        )


async def main():
    """Main server startup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WHIS API Server")
    parser.add_argument("--config", default="ai-training/serve/config.yaml", help="Server config")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--adapter", help="Specific adapter to load")
    
    args = parser.parse_args()
    
    # Create server
    server = WhisAPIServer(args.config)
    
    # Override config with CLI args
    if args.host:
        server.config["server"]["host"] = args.host
    if args.port:
        server.config["server"]["port"] = args.port
    if args.adapter:
        server.config["model"]["auto_load_adapter"] = args.adapter
        
    # Initialize server
    if await server.initialize():
        print(f"🌐 Starting server on {args.host}:{args.port}")
        server.run()
    else:
        print("❌ Server initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())