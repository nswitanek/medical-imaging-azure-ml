# DEC-14 — Orchestration Framework

- **Status:** 🟥 Open
- **Capability:** Multi-step / agentic orchestration of the inference flow
- **Related docs:** [`docs/14`](../docs/14-agentic-orchestration.md)

## Context

The inference flow composes routing, de-ID checks, domain + custom models, retrieval, VLM reasoning, and eval/guardrails. Needs orchestration with tracing, control, and governance.

> **Reference:** Microsoft's [healthcareai-examples](https://github.com/microsoft/healthcareai-examples) shows healthcare vision models wrapped as agent tools — an [MCP plugin for MedImageInsight](https://github.com/microsoft/healthcareai-examples/tree/main/agentic/medimageinsight) with a report-writing agent, and a [classification agent](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/medimageinsight/agent-classification-example.ipynb) using LLM function-calling. Useful patterns regardless of framework chosen below.

## Options

### Option A — Microsoft Foundry Agent Service
**Advantages**
- Managed agent runtime: tool-calling, threads, built-in **tracing/observability**, content safety.
- Tight Azure + Foundry integration; enterprise governance/networking.
- Lowest ops burden; fast to stand up.

**Disadvantages**
- Managed-service constraints; less low-level control than code frameworks.
- Newer service; evolving features.

### Option B — Microsoft Agent Framework (MAF)
**Advantages**
- Code-first (Python/.NET) open-source SDK that **unifies the former Semantic Kernel and AutoGen**; fine-grained control; embeds in existing services.
- Deterministic pipelines where needed; Microsoft-supported, with a clear migration path from Semantic Kernel / AutoGen.

**Disadvantages**
- You build/operate more of the runtime, tracing, and state than a managed service.
- Newer unified framework; APIs still consolidating from the SK/AutoGen lineage.

### Option C — LangGraph (open source, third-party)
**Advantages**
- Most flexible multi-agent graphs; large community; portable across clouds.

**Disadvantages**
- Highest maintenance + governance burden; you own tracing, safety, upgrades.
- Enterprise/compliance hardening is on you.

## Comparison

| Criterion | A: Foundry Agents | B: Microsoft Agent Framework | C: LangGraph |
|---|---|---|---|
| Ops burden | Low | Medium | High |
| Control | Medium | High | High |
| Built-in tracing/safety | Yes | Partial | DIY |
| Azure/governance fit | Native | Good | DIY |
| Time-to-value | Fast | Medium | Medium |

## Recommendation

- **Prototype:** **Foundry Agent Service** (or a thin **Microsoft Agent Framework** pipeline) to prove composition quickly with built-in tracing.
- **Production:** confirm once flows stabilize — Foundry Agents for lowest ops, **Microsoft Agent Framework** where deep code control is needed.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
