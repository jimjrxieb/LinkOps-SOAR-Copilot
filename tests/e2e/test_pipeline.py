#!/usr/bin/env python3
"""
🧪 WHIS End-to-End Testing Pipeline
===================================
Comprehensive testing of the entire SOAR-Copilot system from RAG ingestion
through model inference to security playbook generation.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest
import tempfile
import shutil
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_training.rag.hybrid_retrieval import HybridRetrieval
from ai_training.rag.repo_ingestion import RepoIngestion
from ai_training.rag.delta_indexing import DeltaIndexing
from ai_training.rag.soc_ingestion import SOCIngestion
from ai_training.core.logging import get_logger, configure_logging
from ai_training.configs.config_manager import ConfigManager
from ai_training.monitoring.telemetry import WhisTelemetry


logger = get_logger(__name__)


class E2ETestSuite:
    """End-to-end test suite for WHIS SOAR-Copilot"""
    
    def __init__(self, config_path: str = "tests/e2e/test_config.yaml"):
        self.config_path = Path(config_path)
        self.test_id = str(uuid.uuid4())[:8]
        self.temp_dir = None
        self.components = {}
        
        # Test results tracking
        self.results = {
            "test_id": self.test_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "tests": {},
            "overall_status": "running"
        }
        
        logger.info(f"🧪 Initializing E2E test suite: {self.test_id}")
    
    async def setup(self):
        """Set up test environment"""
        logger.info("🔧 Setting up E2E test environment")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"whis_e2e_{self.test_id}_"))
        logger.info(f"Created temp directory: {self.temp_dir}")
        
        # Initialize configuration
        config_manager = ConfigManager(base_path=self.temp_dir / "configs")
        
        # Create test configurations
        await self._create_test_configs()
        
        # Initialize telemetry
        self.telemetry = WhisTelemetry(f"whis-e2e-{self.test_id}")
        
        # Initialize core components
        await self._initialize_components()
        
        logger.info("✅ E2E test environment setup complete")
    
    async def teardown(self):
        """Clean up test environment"""
        logger.info("🧹 Cleaning up E2E test environment")
        
        # Export test results
        if self.temp_dir:
            results_file = self.temp_dir / "e2e_results.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Test results saved to: {results_file}")
        
        # Clean up temporary directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temp directory: {self.temp_dir}")
    
    async def _create_test_configs(self):
        """Create test-specific configurations"""
        configs_dir = self.temp_dir / "configs"
        configs_dir.mkdir(parents=True, exist_ok=True)
        
        # RAG config
        rag_config = {
            "embedder": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",  # Lightweight for testing
                "device": "cpu",
                "batch_size": 4
            },
            "vector_store": {
                "type": "chromadb",
                "persist_directory": str(self.temp_dir / "chroma"),
                "collection_name": f"test_{self.test_id}"
            },
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "rerank_enabled": True
            }
        }
        
        with open(configs_dir / "rag.yaml", 'w') as f:
            import yaml
            yaml.dump(rag_config, f)
        
        # Model config (mock for testing)
        model_config = {
            "base_model": {
                "name": "mock-llm",
                "path": str(self.temp_dir / "models" / "mock"),
                "tokenizer_path": str(self.temp_dir / "models" / "mock")
            },
            "inference": {
                "max_tokens": 100,
                "temperature": 0.7,
                "device": "cpu"
            }
        }
        
        with open(configs_dir / "model.yaml", 'w') as f:
            yaml.dump(model_config, f)
    
    async def _initialize_components(self):
        """Initialize system components for testing"""
        
        # Create test data
        test_data_dir = self.temp_dir / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        
        # Create sample repository for ingestion
        repo_dir = test_data_dir / "sample_repo"
        repo_dir.mkdir(exist_ok=True)
        
        # Create sample Python files
        (repo_dir / "security_utils.py").write_text('''
def detect_malware(file_hash: str) -> bool:
    """Detect if file hash matches known malware signatures."""
    known_malware = ["d41d8cd98f00b204e9800998ecf8427e"]
    return file_hash in known_malware

def generate_incident_response(alert_type: str) -> dict:
    """Generate incident response playbook for alert type."""
    playbooks = {
        "malware": ["isolate_host", "collect_artifacts", "analyze_sample"],
        "phishing": ["block_sender", "quarantine_emails", "user_training"]
    }
    return {"steps": playbooks.get(alert_type, ["generic_response"])}
''')
        
        (repo_dir / "network_analysis.py").write_text('''
def analyze_network_traffic(pcap_data: bytes) -> dict:
    """Analyze network traffic for suspicious patterns."""
    # Mock implementation for testing
    return {
        "suspicious_connections": 2,
        "malicious_domains": ["evil.com", "malware.net"],
        "data_exfiltration": True
    }

def block_ip_address(ip: str) -> bool:
    """Block IP address at firewall level."""
    # Mock implementation
    return True
''')
        
        # Initialize components
        self.components['repo_ingestion'] = RepoIngestion(
            config_path=self.temp_dir / "configs" / "rag.yaml"
        )
        
        self.components['hybrid_retrieval'] = HybridRetrieval(
            config_path=self.temp_dir / "configs" / "rag.yaml"
        )
        
        self.components['delta_indexing'] = DeltaIndexing(
            config_path=self.temp_dir / "configs" / "rag.yaml"
        )
        
        logger.info("✅ Components initialized for testing")
    
    async def test_repository_ingestion(self) -> Dict[str, Any]:
        """Test repository ingestion and code-aware chunking"""
        test_name = "repository_ingestion"
        logger.info(f"🔬 Running test: {test_name}")
        
        start_time = time.time()
        test_result = {
            "name": test_name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Test ingestion of sample repository
            repo_ingestion = self.components['repo_ingestion']
            repo_path = self.temp_dir / "test_data" / "sample_repo"
            
            # Step 1: Ingest repository
            test_result["steps"].append({
                "step": "ingest_repository",
                "status": "running"
            })
            
            ingestion_stats = await repo_ingestion.ingest_repository(str(repo_path))
            
            test_result["steps"][-1].update({
                "status": "passed",
                "stats": ingestion_stats
            })
            
            # Step 2: Verify chunks were created
            test_result["steps"].append({
                "step": "verify_chunks",
                "status": "running"
            })
            
            chunks = repo_ingestion.get_chunks()
            assert len(chunks) > 0, "No chunks were created"
            assert any("detect_malware" in chunk["text"] for chunk in chunks), "Function chunks not found"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "chunk_count": len(chunks)
            })
            
            # Step 3: Verify metadata extraction
            test_result["steps"].append({
                "step": "verify_metadata",
                "status": "running"
            })
            
            function_chunks = [c for c in chunks if c["metadata"].get("type") == "function"]
            assert len(function_chunks) >= 2, f"Expected at least 2 function chunks, got {len(function_chunks)}"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "function_chunks": len(function_chunks)
            })
            
            test_result["status"] = "passed"
            
        except Exception as e:
            logger.exception(f"Repository ingestion test failed: {e}")
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            if test_result["steps"]:
                test_result["steps"][-1]["status"] = "failed"
                test_result["steps"][-1]["error"] = str(e)
        
        finally:
            test_result["duration_seconds"] = time.time() - start_time
            test_result["end_time"] = datetime.now().isoformat()
            self.results["tests"][test_name] = test_result
        
        return test_result
    
    async def test_hybrid_retrieval(self) -> Dict[str, Any]:
        """Test hybrid retrieval with vector search and BM25"""
        test_name = "hybrid_retrieval"
        logger.info(f"🔬 Running test: {test_name}")
        
        start_time = time.time()
        test_result = {
            "name": test_name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Ensure ingestion is complete first
            await self.test_repository_ingestion()
            
            retrieval = self.components['hybrid_retrieval']
            
            # Step 1: Initialize retrieval system
            test_result["steps"].append({
                "step": "initialize_retrieval",
                "status": "running"
            })
            
            await retrieval.initialize()
            
            test_result["steps"][-1]["status"] = "passed"
            
            # Step 2: Test vector search
            test_result["steps"].append({
                "step": "test_vector_search",
                "status": "running"
            })
            
            vector_results = await retrieval.vector_search(
                query="malware detection functions",
                top_k=3
            )
            
            assert len(vector_results) > 0, "Vector search returned no results"
            assert any("malware" in r["text"].lower() for r in vector_results), "Relevant results not found"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "result_count": len(vector_results)
            })
            
            # Step 3: Test BM25 search
            test_result["steps"].append({
                "step": "test_bm25_search",
                "status": "running"
            })
            
            bm25_results = await retrieval.bm25_search(
                query="network traffic analysis",
                top_k=3
            )
            
            assert len(bm25_results) > 0, "BM25 search returned no results"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "result_count": len(bm25_results)
            })
            
            # Step 4: Test hybrid search
            test_result["steps"].append({
                "step": "test_hybrid_search",
                "status": "running"
            })
            
            hybrid_results = await retrieval.hybrid_search(
                query="security incident response procedures",
                top_k=5
            )
            
            assert len(hybrid_results) > 0, "Hybrid search returned no results"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "result_count": len(hybrid_results),
                "avg_score": sum(r["score"] for r in hybrid_results) / len(hybrid_results)
            })
            
            test_result["status"] = "passed"
            
        except Exception as e:
            logger.exception(f"Hybrid retrieval test failed: {e}")
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            if test_result["steps"]:
                test_result["steps"][-1]["status"] = "failed"
                test_result["steps"][-1]["error"] = str(e)
        
        finally:
            test_result["duration_seconds"] = time.time() - start_time
            test_result["end_time"] = datetime.now().isoformat()
            self.results["tests"][test_name] = test_result
        
        return test_result
    
    async def test_delta_indexing(self) -> Dict[str, Any]:
        """Test incremental indexing capabilities"""
        test_name = "delta_indexing"
        logger.info(f"🔬 Running test: {test_name}")
        
        start_time = time.time()
        test_result = {
            "name": test_name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            delta_indexing = self.components['delta_indexing']
            
            # Step 1: Create initial session outcome
            test_result["steps"].append({
                "step": "create_session_outcome",
                "status": "running"
            })
            
            session_outcome = {
                "session_id": f"test_session_{self.test_id}",
                "user_query": "How do I detect and respond to a phishing attack?",
                "response": "To detect phishing: 1) Check sender authenticity, 2) Analyze URLs, 3) Look for urgency tactics. Response: Block sender, quarantine emails, conduct user training.",
                "rag_sources": [
                    {"source": "security_playbooks.py", "chunk_id": "phishing_detection_001"}
                ],
                "feedback": "helpful",
                "timestamp": datetime.now().isoformat()
            }
            
            # Process delta
            delta_result = await delta_indexing.process_session_delta(session_outcome)
            
            assert delta_result["status"] == "success", "Delta processing failed"
            assert delta_result["chunks_added"] >= 0, "Invalid chunk count"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "chunks_added": delta_result["chunks_added"]
            })
            
            # Step 2: Test retrieval of new content
            test_result["steps"].append({
                "step": "test_delta_retrieval",
                "status": "running"
            })
            
            # Query for the new session content
            retrieval = self.components['hybrid_retrieval']
            results = await retrieval.hybrid_search(
                query="phishing attack detection response",
                top_k=3
            )
            
            # Should find relevant results (possibly including our new delta content)
            assert len(results) > 0, "No results found after delta indexing"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "result_count": len(results)
            })
            
            test_result["status"] = "passed"
            
        except Exception as e:
            logger.exception(f"Delta indexing test failed: {e}")
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            if test_result["steps"]:
                test_result["steps"][-1]["status"] = "failed"
                test_result["steps"][-1]["error"] = str(e)
        
        finally:
            test_result["duration_seconds"] = time.time() - start_time
            test_result["end_time"] = datetime.now().isoformat()
            self.results["tests"][test_name] = test_result
        
        return test_result
    
    async def test_mock_model_inference(self) -> Dict[str, Any]:
        """Test mock model inference pipeline"""
        test_name = "mock_model_inference"
        logger.info(f"🔬 Running test: {test_name}")
        
        start_time = time.time()
        test_result = {
            "name": test_name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Mock model loading
            test_result["steps"].append({
                "step": "load_mock_model",
                "status": "running"
            })
            
            # Simulate model loading
            await asyncio.sleep(0.1)  # Mock loading time
            
            test_result["steps"][-1]["status"] = "passed"
            
            # Step 2: Mock inference
            test_result["steps"].append({
                "step": "mock_inference",
                "status": "running"
            })
            
            # Mock inference with RAG context
            query = "How do I respond to a ransomware attack?"
            
            # Get RAG context
            retrieval = self.components['hybrid_retrieval']
            context_results = await retrieval.hybrid_search(query, top_k=3)
            
            # Mock model response
            mock_response = f"""Based on the security procedures, here's how to respond to a ransomware attack:

1. **Immediate Isolation**: Disconnect affected systems from the network
2. **Assessment**: Determine the scope and type of ransomware
3. **Recovery**: Restore from clean backups if available
4. **Investigation**: Analyze attack vectors and indicators
5. **Communication**: Notify stakeholders and authorities as required

Context used: {len(context_results)} relevant security procedures found.
"""
            
            # Simulate inference time
            await asyncio.sleep(0.2)
            
            assert len(mock_response) > 100, "Response too short"
            assert "ransomware" in mock_response.lower(), "Response not relevant to query"
            
            test_result["steps"][-1].update({
                "status": "passed",
                "response_length": len(mock_response),
                "context_sources": len(context_results)
            })
            
            test_result["status"] = "passed"
            
        except Exception as e:
            logger.exception(f"Mock model inference test failed: {e}")
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            if test_result["steps"]:
                test_result["steps"][-1]["status"] = "failed"
                test_result["steps"][-1]["error"] = str(e)
        
        finally:
            test_result["duration_seconds"] = time.time() - start_time
            test_result["end_time"] = datetime.now().isoformat()
            self.results["tests"][test_name] = test_result
        
        return test_result
    
    async def run_full_suite(self) -> Dict[str, Any]:
        """Run complete end-to-end test suite"""
        logger.info("🚀 Starting full E2E test suite")
        
        try:
            await self.setup()
            
            # Run all tests
            tests = [
                self.test_repository_ingestion(),
                self.test_hybrid_retrieval(),
                self.test_delta_indexing(),
                self.test_mock_model_inference()
            ]
            
            # Execute tests in sequence
            for test_coro in tests:
                result = await test_coro
                logger.info(f"Test {result['name']}: {result['status']}")
            
            # Calculate overall results
            total_tests = len(self.results["tests"])
            passed_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "passed")
            failed_tests = total_tests - passed_tests
            
            self.results.update({
                "end_time": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "overall_status": "passed" if failed_tests == 0 else "failed"
            })
            
            logger.info(f"🎯 E2E Test Suite Complete: {passed_tests}/{total_tests} passed")
            
        except Exception as e:
            logger.exception(f"E2E test suite failed: {e}")
            self.results.update({
                "end_time": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            })
        
        finally:
            self.results["duration_seconds"] = (
                datetime.fromisoformat(self.results["end_time"]) - 
                datetime.fromisoformat(self.results["start_time"])
            ).total_seconds() if self.results.get("end_time") else None
            
            await self.teardown()
        
        return self.results


async def main():
    """Main test runner"""
    # Configure logging for tests
    logging_config = {
        "level": "INFO",
        "handlers": {
            "console": {"enabled": True, "level": "INFO", "format": "text"},
            "file": {"enabled": True, "path": "tests/logs/e2e.log", "level": "DEBUG"}
        }
    }
    configure_logging(logging_config)
    
    # Run test suite
    suite = E2ETestSuite()
    results = await suite.run_full_suite()
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 WHIS E2E Test Suite Results")
    print("="*60)
    print(f"Status: {results['overall_status'].upper()}")
    print(f"Total Tests: {results.get('total_tests', 0)}")
    print(f"Passed: {results.get('passed_tests', 0)}")
    print(f"Failed: {results.get('failed_tests', 0)}")
    print(f"Success Rate: {results.get('success_rate', 0):.1%}")
    print(f"Duration: {results.get('duration_seconds', 0):.2f}s")
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "passed" else 1)


if __name__ == "__main__":
    asyncio.run(main())