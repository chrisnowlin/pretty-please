# Documentation Archive

This directory contains historical documentation from completed implementations and development phases.

## Purpose

These files document the development process and decisions made during implementation. They're archived for historical context but are superseded by the main documentation in `/docs/guides/`, `/docs/features/`, and `/docs/architecture/`.

## October 2025

### Implementation Summaries

- **implementation-summary.md**: RAG enhancement phases 1-3 covering retrieval improvements, context formatting, and generation optimization
- **implementation-complete.md**: Async processing phases 1-5 including ThreadPool offloading, progress tracking, distributed workers, and production deployment
- **enhancements-summary.md**: Async enhancements phases 1-2 for real-time progress updates and WebSocket integration

### Testing & Validation

- **testing-summary.md**: Nanonets migration testing including PowerPoint support, OCR validation, and performance benchmarks
- **debugging-summary.md**: Frontend debugging session for React Query patterns and state management
- **rag-test-findings.md**: RAG enhancement validation including retrieval quality and generation accuracy

### Feature Implementation

- **recommendations-implemented.md**: ESLint configuration and React Query fixes for frontend code quality
- **task-2.1-markdown-parser-report.md**: Markdown parser implementation for Nanonets output processing

### Analysis & Architecture

- **powerpoint-analysis.md**: PowerPoint capability analysis including requirements, architecture design, and integration approach
- **architecture-diagram.txt**: ASCII architecture diagrams showing component interactions and data flow

### Planning Documents

- **next-steps.md**: RAG iteration guidance for incremental improvements

---

## Active Documentation

For current, maintained documentation, please refer to:

- **Getting Started**: [/docs/guides/getting-started.md](../guides/getting-started.md)
- **Async Processing**: [/docs/guides/async-processing.md](../guides/async-processing.md)
- **Nanonets Migration**: [/docs/guides/nanonets-migration.md](../guides/nanonets-migration.md)
- **Citations**: [/docs/features/citations.md](../features/citations.md)
- **Architecture**: [/docs/architecture/system-overview.md](../architecture/system-overview.md)

---

## Archive Policy

Documentation is archived when:
1. It describes completed work that has been integrated into the main codebase
2. It's a temporary summary or status report
3. It's superseded by consolidated documentation

Files are **not** archived when:
1. They describe current features or capabilities
2. They're actively maintained (like README.md)
3. They're referenced from active documentation

---

## Accessing Archived Documentation

All archived files are preserved for:
- Historical reference
- Understanding design decisions
- Troubleshooting legacy issues
- Onboarding new team members

To search archived docs:
```bash
# From project root
rg "search term" docs/archive/
```
