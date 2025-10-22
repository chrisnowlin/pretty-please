# Lesson Plan Markdown Format Specification

This document defines the markdown format for AI-generated lesson plans with source citations and embedded images.

## Overview

Generated lesson plans use **markdown with YAML frontmatter** to provide:
- Clean, readable lesson content
- Inline source citations `[1][2]`
- Embedded images with attribution
- Machine-parseable metadata
- Easy conversion to PDF, HTML, or other formats

## File Structure

```
lesson-plan.md
├── YAML Frontmatter (metadata)
├── Learning Objectives
├── Materials Needed
├── Lesson Flow (with images)
├── Assessment Strategies
├── Differentiation
└── Sources Referenced
```

## YAML Frontmatter

Every lesson begins with YAML frontmatter containing metadata:

```yaml
---
title: "Understanding Fractions: Parts of a Whole"
grade: "3"
subject: "Mathematics"
duration: 50
teaching_style: "balanced"
generated_by_model: "Qwen3-14B-4bit"
generated_at: "2025-10-18T14:30:25"
---
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Descriptive lesson title | "Understanding Fractions" |
| `grade` | string | **Abbreviated** grade level | "3", "K", "6-8", "9-12", "College" |
| `subject` | string | Subject area | "Mathematics", "Science", "English Language Arts" |
| `duration` | integer | Lesson duration in minutes | 50 (default), 20-90 range |
| `teaching_style` | string | Teaching approach | "balanced", "direct", "inquiry", "project" |

### Auto-Generated Fields

| Field | Type | Description |
|-------|------|-------------|
| `generated_by_model` | string | AI model used for generation |
| `generated_at` | string | ISO 8601 timestamp |

## Grade Level Format

**IMPORTANT**: Use abbreviated grade levels only.

✅ **Correct**:
- `grade: "K"`
- `grade: "3"`
- `grade: "6-8"`
- `grade: "9-12"`
- `grade: "College"`

❌ **Incorrect**:
- `grade: "Kindergarten"`
- `grade: "Grade 3"`
- `grade: "Grades 6-8"`
- `grade: "High School"`

## Source Citations

### Inline Citations

**EVERY** fact, concept, or activity **MUST** be cited using bracketed numbers:

```markdown
# Learning Objectives

- Students will understand that fractions represent parts of a whole [1]
- Students will use visual models to represent fractions [1][3]
- Students will compare fractions with like denominators [2]
```

### Multiple Sources

Cite multiple sources by placing citation numbers together:

```markdown
- Use fraction circles to model 1/4, 1/2, 3/4 [1][3]
- Students will complete worksheet problems 1-10 [2]
```

### Citation Rules

1. **Mandatory**: Every substantive claim requires a citation
2. **Accurate**: Only cite sources actually provided
3. **Multiple**: Use multiple citations when combining ideas from different sources
4. **No invention**: Do not fabricate information not in source materials

## Image Inclusion

### Markdown Image Syntax

Images use standard markdown syntax with captions and source attribution:

```markdown
![Fraction circle showing 1/4 shaded](images/fraction_circle.png)
*Figure 1: Circle divided into fourths with one part shaded [Source: [IMG-1]]*
```

### Image Components

1. **Alt text**: Descriptive text for accessibility
   - Example: `![Fraction circle showing 1/4 shaded]`

2. **Image path**: Relative path to image file
   - Example: `(images/fraction_circle.png)`

3. **Caption**: Figure number and description
   - Example: `*Figure 1: Circle divided into fourths with one part shaded*`

4. **Source attribution**: Reference to image source
   - Example: `[Source: [IMG-1]]`

### Full Image Example

```markdown
## Instruction (25 minutes)

Introduce the concept of fractions using visual models [1].

![Fraction circle divided into equal parts](images/fraction_circle.png)
*Figure 1: Fraction circle showing equal partitioning [Source: [IMG-1]]*

Explain that each part represents one piece of the whole [1][3].
```

### Image Placement

- Place images **near relevant content** for pedagogical clarity
- **Materials Needed**: Show required visual aids
- **Instruction**: Illustrate key concepts
- **Practice**: Provide reference diagrams
- Number figures sequentially: Figure 1, Figure 2, etc.

## Source Reference List

Every lesson **MUST** end with a "Sources Referenced" section listing all cited materials.

### Format

```markdown
## Sources Referenced

[1] Chapter 3: Fractions (Textbook.pdf, pages 45-52)
[2] Activities Workbook (Activities.docx)
[3] Visual Models for Fractions (Teaching_Guide.pdf, pages 12-18)
[IMG-1] Fraction Diagrams (Visual_Aids.pptx, slide 5)
[IMG-2] Number Line with Fractions (Diagrams.png)
```

### Citation Format Rules

**Text sources**: `[N] Title (filename, location)`

Examples:
- `[1] Chapter 3: Fractions (Textbook.pdf, pages 45-52)`
- `[2] Activities Workbook (Activities.docx)`
- `[3] Understanding Fractions (Worksheet.pdf)`

**Image sources**: `[IMG-N] Description (filename, location)`

Examples:
- `[IMG-1] Fraction Diagrams (Visual_Aids.pptx, slide 5)`
- `[IMG-2] Number Line (Diagrams.png)`

## Complete Example

```markdown
---
title: "Understanding Fractions: Parts of a Whole"
grade: "3"
subject: "Mathematics"
duration: 50
teaching_style: "balanced"
generated_by_model: "Qwen3-14B-4bit"
generated_at: "2025-10-18T14:30:25"
---

# Learning Objectives

- Students will understand that fractions represent parts of a whole [1]
- Students will use visual models (circles, bars) to represent fractions [1][3]
- Students will identify numerator and denominator in a fraction [2]

# Materials Needed

- Fraction circles (1 set per student) [1]
- Activity worksheet (1 per student) [2]
- Whiteboard and markers [1]

![Fraction circle manipulative](images/fraction_circles.png)
*Figure 1: Fraction circle manipulative set [Source: [IMG-1]]*

# Lesson Flow

## Engagement (5 minutes)

Show students a pizza and ask: "If we cut this pizza into 4 equal slices and eat 1 slice, what fraction did we eat?" [1]

- Allow students to share ideas
- Guide discussion toward "one out of four parts"

## Instruction (25 minutes)

Introduce fractions using visual models [1].

![Fraction circle showing 1/4](images/fraction_circle_quarters.png)
*Figure 2: Circle divided into fourths [Source: [IMG-1]]*

Explain that a fraction has two parts [2]:
- **Numerator**: Number of parts we have (top number)
- **Denominator**: Total number of equal parts (bottom number)

Model several examples using fraction circles [1][3]:
- 1/2: One part out of two equal parts
- 1/4: One part out of four equal parts
- 3/4: Three parts out of four equal parts

![Number line with fractions](images/number_line_fractions.png)
*Figure 3: Number line showing fractions between 0 and 1 [Source: [IMG-2]]*

## Practice (15 minutes)

Distribute fraction circles and worksheets [2].

Students work individually to:
1. Create fraction models for: 1/2, 1/3, 2/3, 1/4, 3/4
2. Draw and label fractions on worksheet
3. Identify numerator and denominator in given fractions

Circulate to provide support [1].

## Closure (5 minutes)

Exit ticket: Draw a fraction circle showing 2/4 and label the numerator and denominator [2].

- Collect exit tickets to assess understanding
- Preview next lesson: comparing fractions

# Assessment Strategies

- **Formative**: Monitor student responses during instruction [1]
- **Practice check**: Review worksheet completion and accuracy [2]
- **Exit ticket**: Assess understanding of numerator/denominator [2]

# Differentiation

- **Support**: Provide pre-divided circles for struggling students [3]
- **Extension**: Challenge advanced students to find equivalent fractions (e.g., 2/4 = 1/2) [3]
- **ELL**: Use visual models extensively and provide fraction vocabulary cards [1]

# Sources Referenced

[1] Chapter 3: Fractions (Math_Textbook.pdf, pages 45-52)
[2] Fraction Activities Workbook (Activities.docx)
[3] Visual Models for Teaching Fractions (Teaching_Guide.pdf, pages 12-18)
[IMG-1] Fraction Circle Diagrams (Visual_Aids.pptx, slide 5)
[IMG-2] Number Line with Fractions (Fraction_Diagrams.png)
```

## Markdown Formatting Guidelines

### Headers

- `# ` for major sections (Learning Objectives, Lesson Flow)
- `## ` for subsections (Engagement, Instruction, Practice, Closure)
- `### ` for minor subsections (if needed)

### Lists

**Unordered lists**: Use `-` for bullet points

```markdown
- First item
- Second item
  - Nested item
```

**Ordered lists**: Use `1.` for numbered steps

```markdown
1. First step
2. Second step
3. Third step
```

### Emphasis

- **Bold** for key terms: `**numerator**`
- *Italic* for image captions: `*Figure 1: Description*`
- `Code formatting` for specific instructions: `` `Write 3/4 on your paper` ``

### Spacing

- Include **blank lines** between sections
- Keep paragraphs **concise** (2-4 sentences)
- Use spacing to improve readability

## Validation Checklist

Before finalizing a lesson, verify:

- [ ] YAML frontmatter includes all required fields
- [ ] Grade is in abbreviated format (e.g., "3", not "Grade 3")
- [ ] Duration is set (default: 50 minutes)
- [ ] Every fact has at least one citation [1][2]
- [ ] All images included with `![alt](path)` syntax
- [ ] Image captions include source attribution `[Source: [IMG-1]]`
- [ ] "Sources Referenced" section at end
- [ ] All citation numbers used appear in source list
- [ ] No fabricated sources or content
- [ ] Markdown is clean and properly formatted

## Converting to Other Formats

### PDF Export

Use tools like Pandoc or markdown-pdf:

```bash
pandoc lesson.md -o lesson.pdf --pdf-engine=xelatex
```

### HTML Export

```bash
pandoc lesson.md -o lesson.html --standalone
```

### DOCX Export

```bash
pandoc lesson.md -o lesson.docx
```

## Best Practices

1. **Citation density**: Aim for at least 1 citation every 2-3 sentences
2. **Image relevance**: Only include images that enhance learning
3. **Source variety**: Use multiple sources to provide comprehensive coverage
4. **Readability**: Keep markdown clean and easy to parse
5. **Accuracy**: Never invent content not present in source materials
6. **Attribution**: Always credit source materials properly

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Related**: [Educational Data Models](../src/jina_rag_pipeline/models/educational.py), [Lesson Prompts](../src/jina_rag_pipeline/generation/educational_prompts.py)
