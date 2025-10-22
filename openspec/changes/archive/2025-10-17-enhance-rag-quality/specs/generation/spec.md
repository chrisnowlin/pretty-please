# generation Capability Specification

## Purpose
Enhanced prompting and response formatting for improved citation quality, markdown formatting, and confidence communication.

## ADDED Requirements

### Requirement: Structured Citation System
The system SHALL provide numbered citation format for source attribution.

#### Scenario: Generate numbered citations for text sources
- **WHEN** formatting context for LLM
- **THEN** assigns sequential numbers to text sources [1], [2], [3]...
- **AND** includes citation ID at start of each source block
- **AND** preserves source metadata (filename, page, relevance)

#### Scenario: Generate image citations
- **WHEN** formatting image context for LLM
- **THEN** assigns image citation IDs like [IMG-1], [IMG-2]
- **AND** includes image metadata (filename, description, dimensions)
- **AND** separates image citations from text citations clearly

#### Scenario: Instruct LLM on citation usage
- **WHEN** building system prompt with citations
- **THEN** includes explicit instructions for citing sources
- **AND** provides examples of inline citation format
- **AND** requires citations for all factual claims from context

### Requirement: Enhanced Context Formatting
The system SHALL format retrieved context with rich metadata and structure.

#### Scenario: Format context with metadata
- **WHEN** presenting retrieved documents to LLM
- **THEN** includes source name and type
- **AND** includes relevance score for transparency
- **AND** includes document metadata (date, author, page if available)
- **AND** uses consistent markdown structure

#### Scenario: Separate modalities clearly
- **WHEN** context includes both text and images
- **THEN** groups text sources in dedicated section
- **AND** groups image sources in dedicated section
- **AND** uses visual separators between sections
- **AND** maintains clear citation namespace separation

#### Scenario: Highlight high-relevance sources
- **WHEN** relevance scores are available
- **THEN** sorts sources by relevance (highest first)
- **AND** displays relevance scores in consistent format (0.XX)
- **AND** optionally marks very high relevance (>0.90) for emphasis

### Requirement: Response Formatting Guidelines
The system SHALL instruct LLM on proper response formatting.

#### Scenario: Markdown formatting instructions
- **WHEN** building system prompt
- **THEN** includes guidelines for using headers (##, ###)
- **AND** includes guidelines for lists (ordered, unordered)
- **AND** includes guidelines for emphasis (**bold**, *italic*)
- **AND** includes guidelines for code blocks and inline code

#### Scenario: Citation format instructions
- **WHEN** instructing LLM on citations
- **THEN** specifies inline citation format: "According to [1], ..."
- **AND** specifies multi-source citation: "Multiple sources [1][3] indicate..."
- **AND** provides citation examples in system prompt
- **AND** requires citations for all context-derived information

#### Scenario: Table formatting for comparisons
- **WHEN** system prompt is generated
- **THEN** includes instructions for using markdown tables
- **AND** provides example table structure
- **AND** suggests tables for comparing information across sources

### Requirement: Confidence Communication
The system SHALL guide LLM to express uncertainty appropriately.

#### Scenario: Partial information handling
- **WHEN** context is incomplete
- **THEN** instructs LLM to acknowledge limitations
- **AND** provides template: "Based on available context [1][2], I can partially answer..."
- **AND** encourages specific statements about what is/isn't covered

#### Scenario: High uncertainty handling
- **WHEN** context doesn't definitively answer query
- **THEN** instructs LLM to express uncertainty clearly
- **AND** provides template: "The context suggests... but doesn't provide definitive information"
- **AND** prevents fabrication of information

#### Scenario: No relevant context
- **WHEN** retrieved context is not relevant
- **THEN** instructs LLM to acknowledge lack of relevant information
- **AND** provides template: "I don't find relevant information in the provided context"
- **AND** prevents hallucination attempts

### Requirement: Prompt Template Management
The system SHALL maintain versioned prompt templates for different use cases.

#### Scenario: Select prompt by context type
- **WHEN** generating response with text-only context
- **THEN** uses text-optimized prompt template
- **AND** includes text-specific citation instructions

#### Scenario: Select multimodal prompt
- **WHEN** generating response with images in context
- **THEN** uses multimodal prompt template
- **AND** includes image citation instructions
- **AND** explains image reference limitations (text-based descriptions)

#### Scenario: Apply custom instructions
- **WHEN** session or user has custom prompt instructions
- **THEN** appends custom instructions to base prompt
- **AND** maintains consistent structure
- **AND** validates instruction safety

## MODIFIED Requirements

### Requirement: System Prompts (existing in prompts.py)
The system SHALL provide enhanced system prompts with citation and formatting guidance.

#### Scenario: Enhanced default prompt
- **WHEN** building system prompt for text-based RAG
- **THEN** includes original helpful assistant instructions
- **AND** adds structured citation requirements
- **AND** adds markdown formatting guidelines
- **AND** adds confidence expression templates
- **AND** provides concrete examples of good responses

#### Scenario: Enhanced multimodal prompt
- **WHEN** building system prompt for multimodal RAG
- **THEN** includes all text-based enhancements
- **AND** adds image citation format ([IMG-N])
- **AND** explains image description limitations
- **AND** provides multimodal response examples

## ADDED Requirements (Context Formatter)

### Requirement: Formatted Context Output
The system SHALL produce consistently formatted context strings.

#### Scenario: Generate citation-ready text context
- **WHEN** formatting text results
- **THEN** produces format: "[N] **Source**: {source} | **Relevance**: {score}\n{content}\n\n"
- **AND** numbers citations sequentially
- **AND** includes all metadata fields

#### Scenario: Generate citation-ready image context
- **WHEN** formatting image results
- **THEN** produces format: "[IMG-N] **File**: {filename} | **Description**: {desc} | **Relevance**: {score}\n\n"
- **AND** numbers image citations separately
- **AND** includes dimension and format metadata

#### Scenario: Combine text and image context
- **WHEN** both text and images are present
- **THEN** outputs "**Text Sources:**\n" section first
- **AND** outputs "**Image Sources:**\n" section second
- **AND** separates sections with "---\n\n"
- **AND** maintains clear visual hierarchy

## Relationships
- **Uses**: `retrieval` (formats output from enhanced retrieval)
- **Used by**: `api` (chat endpoint uses enhanced prompts and formatting)
- **Extends**: Existing generation module (QwenGenerator, ContextFormatter, prompts)
