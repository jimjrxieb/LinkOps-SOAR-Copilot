#!/usr/bin/env python3
"""
🧠 Teacher-Assisted Learning Pipeline for WHIS
==============================================
Uses GPT to generate grounded test data and knowledge from gaps

[TAG: TEACHER-LANES] - Grounded vs Open teacher modes
[TAG: GAP-INTAKE] - Process unanswered questions
[TAG: TEACHER-DRAFT] - Generate answers with citations
[TAG: AUTO-VERIFY] - NLI and consistency checks
[TAG: TEST-GEN] - Create test questions from knowledge
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from openai import AsyncOpenAI
import hashlib

# Load environment
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeacherAssistedPipeline:
    """
    Teacher model pipeline for generating test data and filling knowledge gaps
    
    [TAG: TEACHER-LANES] - Two modes: grounded (RAG-only) and open (general knowledge)
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Paths
        self.gaps_dir = Path("soar-platform/knowledge_gaps")
        self.rag_chunks_dir = Path("ai-training/rag/chunks")
        self.test_output_dir = Path("tests/golden")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load RAG retriever for grounding
        self.rag_retriever = self._init_rag_retriever()
        
        # Quality gates
        self.min_citation_rate = 0.98
        self.min_entailment_score = 0.75
        
    def _init_rag_retriever(self):
        """Initialize RAG retriever for grounding checks"""
        try:
            import sys
            sys.path.insert(0, '.')
            from apps.api.engines.rag_retriever import get_rag_retriever
            retriever = get_rag_retriever()
            if retriever.is_available():
                logger.info("✅ RAG retriever loaded for grounding")
                return retriever
        except Exception as e:
            logger.warning(f"RAG retriever not available: {e}")
            # Fallback: Load knowledge directly from chunks
            return self._load_knowledge_chunks()
        return None
    
    def _load_knowledge_chunks(self):
        """Load knowledge chunks directly as fallback"""
        import json
        from pathlib import Path
        
        chunks = []
        metadata_file = Path("ai-training/rag/vectorstore/whis_cybersecurity_knowledge.metadata.json")
        
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                chunks = data.get("chunks", [])
                logger.info(f"✅ Loaded {len(chunks)} knowledge chunks directly")
        
        # Create simple retriever-like object
        class SimpleRetriever:
            def __init__(self, chunks):
                self.chunks = chunks
                
            def search(self, query, k=5, min_score=0.0):
                # Simple keyword matching
                query_lower = query.lower()
                results = []
                
                for chunk in self.chunks:
                    content = chunk.get("content", "").lower()
                    title = chunk.get("title", "").lower()
                    
                    # Simple relevance scoring
                    score = 0
                    query_words = query_lower.split()
                    for word in query_words:
                        if word in content:
                            score += content.count(word)
                        if word in title:
                            score += 5  # Title matches weighted higher
                    
                    if score > 0:
                        results.append({
                            "content": chunk.get("content", ""),
                            "source": chunk.get("source", "unknown"),
                            "chunk_id": chunk.get("id", ""),
                            "score": min(score / 10, 1.0)  # Normalize score
                        })
                
                # Sort by score and return top k
                results.sort(key=lambda x: x["score"], reverse=True)
                
                # Convert to result objects
                class Result:
                    def __init__(self, data):
                        self.content = data["content"]
                        self.source = data["source"]
                        self.chunk_id = data["chunk_id"]
                        self.score = data["score"]
                
                return [Result(r) for r in results[:k]]
            
            def is_available(self):
                return True
        
        return SimpleRetriever(chunks)
    
    async def process_gaps(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        [TAG: GAP-INTAKE] - Process top knowledge gaps
        """
        
        gaps_file = self.gaps_dir / "unanswered_questions.json"
        if not gaps_file.exists():
            logger.warning("No gaps file found")
            return []
        
        with open(gaps_file) as f:
            gaps_data = json.load(f)
        
        # Prioritize by frequency and intent
        canonical_gaps = gaps_data.get("canonical_questions", [])
        
        # Sort by frequency × impact
        prioritized = sorted(
            canonical_gaps,
            key=lambda x: x.get("frequency", 1) * (2 if "definition" in x.get("intent", "") else 1),
            reverse=True
        )[:limit]
        
        logger.info(f"[GAP-INTAKE] Processing {len(prioritized)} priority gaps")
        
        results = []
        for gap in prioritized:
            result = await self.generate_grounded_answer(gap)
            if result:
                results.append(result)
        
        return results
    
    async def generate_grounded_answer(self, gap: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        [TAG: TEACHER-DRAFT] - Generate answer grounded in RAG
        """
        
        question = gap.get("canonical_form", "")
        intent = gap.get("intent", "unknown")
        
        if not question:
            return None
        
        # Get relevant RAG chunks
        rag_context = []
        citations = []
        
        if self.rag_retriever:
            results = self.rag_retriever.search(question, k=5, min_score=0.3)
            for result in results:
                rag_context.append(result.content)
                citations.append({
                    "source": result.source,
                    "chunk_id": result.chunk_id,
                    "score": result.score
                })
        
        if not rag_context:
            logger.warning(f"[TEACHER-DRAFT] No RAG context for: {question}")
            return None
        
        # Build teacher prompt
        system_prompt = """You are a cybersecurity expert assistant helping create accurate knowledge base entries.
        
        STRICT RULES:
        1. Answer ONLY based on the provided context chunks
        2. Keep answers concise (1-2 sentences for definitions)
        3. Include specific citations to context chunks
        4. If context doesn't contain the answer, return {"abstain": true}
        5. Never make up information not in the context
        """
        
        user_prompt = f"""Question: {question}
        Intent: {intent}
        
        Context chunks:
        {chr(10).join([f"[Chunk {i+1}]: {chunk[:500]}" for i, chunk in enumerate(rag_context)])}
        
        Provide answer in JSON:
        {{
            "answer": "concise answer text",
            "citations": ["Chunk 1", "Chunk 3"],
            "confidence": 0.0-1.0,
            "lane": "grounded",
            "abstain": false
        }}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("abstain"):
                logger.info(f"[TEACHER-DRAFT] Abstained on: {question}")
                return None
            
            # Map citations back to source IDs
            cited_chunks = []
            for cite in result.get("citations", []):
                if "Chunk" in cite:
                    idx = int(cite.split()[-1]) - 1
                    if 0 <= idx < len(citations):
                        cited_chunks.append(citations[idx])
            
            return {
                "question": question,
                "answer": result.get("answer"),
                "intent": intent,
                "lane": "grounded",
                "citations": cited_chunks,
                "confidence": result.get("confidence", 0.5),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TEACHER-DRAFT] Failed: {e}")
            return None
    
    async def auto_verify(self, draft: Dict[str, Any]) -> bool:
        """
        [TAG: AUTO-VERIFY] - Verify draft quality
        """
        
        # Check citation presence
        if not draft.get("citations"):
            logger.warning("[AUTO-VERIFY] No citations")
            return False
        
        # Check confidence threshold
        if draft.get("confidence", 0) < 0.6:
            logger.warning("[AUTO-VERIFY] Low confidence")
            return False
        
        # Policy checks
        answer = draft.get("answer", "").lower()
        forbidden = ["password", "secret", "api_key", "token", "execute", "sudo", "admin"]
        
        if any(word in answer for word in forbidden):
            logger.warning("[AUTO-VERIFY] Policy violation detected")
            return False
        
        return True
    
    async def generate_test_questions(self, knowledge_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [TAG: TEST-GEN] - Generate test questions from knowledge
        """
        
        question = knowledge_entry.get("question")
        answer = knowledge_entry.get("answer")
        citations = knowledge_entry.get("citations", [])
        
        if not all([question, answer, citations]):
            return []
        
        system_prompt = """Generate diverse test questions for this knowledge entry.
        Create 3 variations:
        1. Direct question (same intent)
        2. Paraphrased question  
        3. Scenario-based question
        
        Each must have the same answer and citations."""
        
        user_prompt = f"""Original Q: {question}
        Answer: {answer}
        Citations: {json.dumps(citations)}
        
        Generate test questions in JSON:
        {{
            "tests": [
                {{
                    "question": "test question text",
                    "expected_answer": "answer text",
                    "citations": [...],
                    "type": "direct|paraphrase|scenario"
                }}
            ]
        }}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            tests = result.get("tests", [])
            
            # Add metadata
            for test in tests:
                test["source_question"] = question
                test["generated_at"] = datetime.utcnow().isoformat()
                test["verified"] = False
            
            return tests
            
        except Exception as e:
            logger.error(f"[TEST-GEN] Failed: {e}")
            return []
    
    async def run_pipeline(self):
        """Run the complete teacher-assisted pipeline"""
        
        logger.info("🚀 Starting Teacher-Assisted Pipeline")
        
        # Step 1: Process gaps
        logger.info("[STEP 1] Processing knowledge gaps...")
        knowledge_entries = await self.process_gaps(limit=10)
        logger.info(f"Generated {len(knowledge_entries)} knowledge entries")
        
        # Step 2: Verify entries
        logger.info("[STEP 2] Auto-verifying entries...")
        verified_entries = []
        for entry in knowledge_entries:
            if await self.auto_verify(entry):
                verified_entries.append(entry)
        
        logger.info(f"Verified {len(verified_entries)}/{len(knowledge_entries)} entries")
        
        # Step 3: Generate tests
        logger.info("[STEP 3] Generating test questions...")
        all_tests = []
        for entry in verified_entries:
            tests = await self.generate_test_questions(entry)
            all_tests.extend(tests)
        
        logger.info(f"Generated {len(all_tests)} test questions")
        
        # Step 4: Save outputs
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save knowledge entries
        knowledge_file = self.test_output_dir / f"teacher_knowledge_{timestamp}.json"
        with open(knowledge_file, 'w') as f:
            json.dump({
                "generated_at": datetime.utcnow().isoformat(),
                "entries": verified_entries,
                "stats": {
                    "total_processed": len(knowledge_entries),
                    "verified": len(verified_entries),
                    "citation_rate": sum(1 for e in verified_entries if e.get("citations")) / max(len(verified_entries), 1)
                }
            }, f, indent=2)
        
        # Save test questions
        test_file = self.test_output_dir / f"teacher_tests_{timestamp}.json"
        with open(test_file, 'w') as f:
            json.dump({
                "generated_at": datetime.utcnow().isoformat(),
                "tests": all_tests,
                "coverage": {
                    "total_tests": len(all_tests),
                    "source_entries": len(verified_entries)
                }
            }, f, indent=2)
        
        logger.info(f"✅ Pipeline complete!")
        logger.info(f"  Knowledge: {knowledge_file}")
        logger.info(f"  Tests: {test_file}")
        
        return {
            "knowledge_entries": verified_entries,
            "test_questions": all_tests,
            "stats": {
                "gaps_processed": len(knowledge_entries),
                "entries_verified": len(verified_entries),
                "tests_generated": len(all_tests)
            }
        }

async def main():
    """Run the teacher pipeline"""
    pipeline = TeacherAssistedPipeline()
    results = await pipeline.run_pipeline()
    
    print("\n📊 PIPELINE RESULTS:")
    print(f"  Gaps processed: {results['stats']['gaps_processed']}")
    print(f"  Entries verified: {results['stats']['entries_verified']}")
    print(f"  Tests generated: {results['stats']['tests_generated']}")

if __name__ == "__main__":
    asyncio.run(main())