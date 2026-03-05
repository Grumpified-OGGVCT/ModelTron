# ⚖ ModelTron Engine: Enterprise Model Ranking System
## Complete Specification Document (Unabbreviated)

**Version:** 2026.1 (Enterprise Edition)
**Verification Date:** March 2026
**Status:** Production-Ready Specification
**Authority:** This document operates under principles of truth, integrity, and accuracy in all technical claims.

[![CI](https://github.com/Grumpified-OGGVCT/ModelTron/actions/workflows/ci.yml/badge.svg)](https://github.com/Grumpified-OGGVCT/ModelTron/actions/workflows/ci.yml)
[![Demo](https://img.shields.io/badge/demo-GitHub_Pages-blue)](https://grumpified-oggvct.github.io/ModelTron/)
[![License](https://img.shields.io/github/license/Grumpified-OGGVCT/ModelTron)](LICENSE)

**[🌐 Live Demo & Leaderboard →](https://grumpified-oggvct.github.io/ModelTron/)**

---

## 1. Executive Summary

### 1.1 Purpose Statement

The **ModelTron Engine** is an enterprise-grade model ranking system designed for **accuracy-first evaluation**. Unlike traditional leaderboards that rely on static benchmarks or LLM-as-judge approaches (prone to hallucination and bias), ModelTron uses a **deterministic verification pipeline** where smart LLMs generate test rubrics, but code execution verifies results.

### 1.2 Core Design Principles

| **Principle** | **Implementation** | **Rationale** |
|---------------|-------------------|---------------|
| **Accuracy Over Speed** | Deterministic code execution for grading | Eliminates LLM hallucination in scoring |
| **Transparency** | All rubrics human-reviewed before deployment | Ensures test validity |
| **Dynamic Testing** | Procedurally generated test cases at runtime | Prevents benchmark memorization |
| **Multi-Dimensional** | 8 capability categories with weighted scoring | Reflects real-world usage patterns |
| **Agent-Accessible** | `/v1/recommend` API for programmatic selection | Enables autonomous system integration |

### 1.3 Final Model Selection (Verified)

| **Role** | **Selected Model** | **Verified Specs** | **Primary Category** |
| :--- | :--- | :--- | :--- |
| **Primary Orchestrator** | `deepseek-v3.2:cloud` | Hybrid thinking/non-thinking mode | Reasoning & Logic |
| **Secondary Orchestrator** | `glm-5:cloud` | 744B total/40B active, 128K context | Structured Outputs & Security |
| **Coding Specialist** | `minimax-m2.5:cloud` | SOTA productivity/coding | Code Generation |
| **Multimodal Specialist** | `qwen3-vl:235b-cloud` | 90.0% MMLU-Pro verified | Multimodal Processing |
| **Agentic/Mixed Tasks** | `qwen3.5:397b-cloud` | 78.6% BrowseComp, 256K+ context | Agentic Workflows |
| **Edge Agent** | `qwen3-coder-next:cloud` | Coding-focused, IDE integration | Local Sandbox Execution |
| **Context/RAG Specialist** | `gemini-3-flash-preview:cloud` | 1M-token context | Context Management |
| **Performance/Efficiency** | `ministral-3:3b-cloud` | Edge deployment optimized | Performance & Efficiency |

---

## 2. System Architecture Overview

### 2.1 Component Description

| **Layer** | **Component** | **Function** | **Technology** |
|-----------|---------------|--------------|----------------|
| **Ingestion** | Capability Router | Categorizes incoming evaluation tasks | Custom routing logic |
| **Intelligence** | Rubric Generators | Create test harnesses for each category | DeepSeek-V3.2, GLM-5, MiniMax-M2.5, Qwen3-VL |
| **Intelligence** | Human Review Loop | Validates rubric logic before deployment | Manual review interface |
| **Sandbox** | Firecracker microVMs | Isolates code execution securely | AWS Firecracker / Local Docker |
| **Sandbox** | Runtime Environments | Executes candidate model outputs | Python, Node.js, Shell |
| **Verification** | Deterministic Graders | Produces pass/fail binary scores | Unit tests, schema validators |
| **Output** | API Endpoints | Serves rankings to downstream systems | FastAPI / REST |
| **Output** | Dynamic Leaderboard | Real-time visualization of model performance | Web dashboard (docs/index.html) |

---

## 3. Quick Start

### Prerequisites

- Python 3.12+ with `pip`
- An Ollama endpoint (auto-detected at `http://localhost:11434` via setup wizard).

### Installation

```bash
# 1. Clone & install
git clone https://github.com/Grumpified-OGGVCT/ModelTron.git
cd ModelTron
pip install -r requirements.txt

# 2. Run Setup Wizard
python scripts/setup_wizard.py

# 3. Launch the API Server
python main.py
```

---

## 4. API Endpoints

| **Endpoint** | **Method** | **Description** |
|--------------|------------|-----------------|
| `/v1/evaluate/{category}` | POST | Submit model for category evaluation |
| `/v1/recommend` | GET | Get model recommendation for use case |
| `/v1/rankings` | GET | Retrieve current model rankings |
| `/v1/benchmarks` | GET | List available benchmark suites |
| `/v1/health` | GET | System health check |

---

## 5. Deployment Roadmap

- **Phase 1: Infrastructure** (Sandbox execution)
- **Phase 2: Deterministic Harness** (Unit test generators)
- **Phase 3: Category Test Suites** (All 8 capability evaluations)
- **Phase 4: API Development** (All /v1/* endpoints)
- **Phase 5: Public Release** (Leaderboard update)

For the full specification, 8 primary categories, and industry specific use-case matrix, please refer to the internal documentation and `AGENTS.md`.
