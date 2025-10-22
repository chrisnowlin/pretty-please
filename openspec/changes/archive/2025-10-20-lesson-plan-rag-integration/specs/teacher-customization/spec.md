# Specification: Teacher Customization & Control

**Change ID**: `lesson-plan-rag-integration`
**Capability**: Teacher Customization & Control
**Phase**: 2
**Status**: Draft

## Overview

Teachers can customize and refine generated lessons to match their specific classroom needs. Customizations include duration adjustment, teaching style changes, differentiation options, and component-level regeneration.

## ADDED Requirements

#### Requirement: Adjust Lesson Duration
**Description**: Teacher can change lesson duration and system adjusts activities accordingly.

**Scenario**: System generates 45-minute lesson. Teacher changes to 30 minutes. System:
1. Proportionally reduces phase durations
2. Removes or consolidates activities
3. Maintains pedagogical structure
4. Regenerates activities for new duration

**Acceptance Criteria**:
- [ ] Duration adjustment: 20-90 minutes supported
- [ ] Activity count reduces with duration (not just speed up)
- [ ] Total time matches requested duration
- [ ] Learning objectives remain achievable
- [ ] Teachers report modified lessons are still usable

#### Requirement: Change Teaching Style
**Description**: Teacher can switch lesson between teaching styles and activities regenerate.

**Scenario**: 45-minute "direct instruction" lesson on fractions. Teacher switches to "inquiry-based":
1. Engagement phase becomes investigative question
2. Instruction becomes student discovery
3. Practice becomes guided inquiry
4. Assessments become performance-based
5. Materials change to support inquiry

**Acceptance Criteria**:
- [ ] All teaching styles supported: direct, inquiry, project, balanced
- [ ] Activities match selected style
- [ ] Timing remains within duration
- [ ] Standards alignment preserved
- [ ] Pedagogical approach consistent throughout

#### Requirement: Add Student Population Modifications
**Description**: Teacher specifies student population and system adjusts lesson for their needs.

**Scenario**: Teacher specifies "Mostly ELL learners, mixed levels". System:
1. Modifies vocabulary and language complexity
2. Adds visual aids and word banks
3. Includes peer support strategies
4. Suggests scaffolding techniques
5. Provides cultural responsiveness tips

**Acceptance Criteria**:
- [ ] Modifications for: ELL, special education, gifted, mixed SES
- [ ] Modifications are practical and implementable
- [ ] Vocabulary adjustment is appropriate
- [ ] Cultural responsiveness included
- [ ] Teachers find modifications helpful (feedback)

#### Requirement: Customize Assessment Approach
**Description**: Teacher can specify assessment type and lesson regenerates with appropriate assessments.

**Scenario**: Teacher specifies "Performance-based summative". System:
1. Removes multiple-choice questions
2. Adds project deliverables
3. Includes rubric for performance assessment
4. Provides portfolio reflection prompts
5. Adds peer/self-assessment components

**Acceptance Criteria**:
- [ ] Assessment types: formative, summative, diagnostic, performance
- [ ] Assessment methods vary by type
- [ ] Rubrics or answer keys provided
- [ ] Formative assessments included alongside selected type
- [ ] Teachers can modify rubrics in UI

#### Requirement: Regenerate Individual Components
**Description**: Teacher can regenerate specific lesson components without changing entire lesson.

**Scenario**: Teacher likes activities but wants different opening engagement. System:
1. Teacher clicks "Regenerate engagement phase"
2. System regenerates just that phase
3. Keeps all other phases unchanged
4. Same duration, same standard alignment
5. New engagement options presented

**Acceptance Criteria**:
- [ ] Components regeneratable individually: engagement, activities, assessments, closure
- [ ] Regeneration preserves other components
- [ ] Duration constraints maintained
- [ ] Multiple regeneration options shown (3-5 variations)
- [ ] Teacher can accept or regenerate again

#### Requirement: Save Custom Lesson Versions
**Description**: Teacher can save customized lessons and create new versions.

**Scenario**: Teacher customizes lesson, saves as v1.0. Later:
1. Teacher modifies again, saves as v1.1
2. Can revert to any previous version
3. Can compare versions side-by-side
4. Can restore from trash if accidentally deleted

**Acceptance Criteria**:
- [ ] Version history stored (at least 10 versions)
- [ ] Version names: auto-timestamp + teacher notes
- [ ] Versions comparable in UI
- [ ] Restore from previous version works
- [ ] Lessons stay organized (not messy version history)

#### Requirement: Share Customizations
**Description**: Teacher can share customized lessons with colleagues.

**Scenario**: Teacher creates great fractions lesson, customized for ELL. Teacher:
1. Selects "Share" → generates shareable link
2. Colleague accesses link, sees lesson
3. Colleague can duplicate and customize further
4. Original teacher credited and notified

**Acceptance Criteria**:
- [ ] Share generates public link (24-hour expiry by default)
- [ ] Shared lesson read-only (recipient must duplicate to modify)
- [ ] Recipient can duplicate to their own lessons
- [ ] Creator notified when lesson shared
- [ ] Share statistics tracked (optional)

#### Requirement: Provide Optimization Suggestions
**Description**: System suggests improvements to customized lessons.

**Scenario**: Teacher creates lesson but misses some opportunities. System:
- Suggests: "This objective could include a peer discussion activity"
- Suggests: "Consider adding this related standard (cross-curricular link)"
- Suggests: "Struggling learners might benefit from manipulatives here"
- Suggests: "This assessment aligns strongly to standard XYZ"

**Acceptance Criteria**:
- [ ] Suggestions appear after generation or customization
- [ ] Suggestions are actionable (teacher can apply with one click)
- [ ] Suggestions don't overwhelm (max 3-5 per lesson)
- [ ] Teacher can dismiss/hide suggestions
- [ ] Suggestions improve pedagogical quality

#### Requirement: Export Customized Lessons
**Description**: Customized lessons export with all modifications intact.

**Scenario**: Teacher customizes lesson extensively, then exports:
- Markdown export preserves all customizations, formatting
- PDF export is professional, print-ready
- JSON export includes metadata about customizations
- Export complete in <5 seconds

**Acceptance Criteria**:
- [ ] All export formats support customized lessons
- [ ] No data lost in export
- [ ] Customization metadata preserved
- [ ] Export file size reasonable (<5MB even for large lessons)
- [ ] Formatting consistent across formats

## MODIFIED Requirements

*(No modifications to existing requirements)*

## REMOVED Requirements

*(No removals)*

## Implementation Notes

### Customization Request Schema

```python
@dataclass
class CustomizationRequest:
    """Teacher customization parameters."""
    lesson_id: str

    # Optional customizations (null = don't change)
    duration_minutes: Optional[int]
    teaching_style: Optional[str]      # "direct" | "inquiry" | "project" | "balanced"
    student_population: Optional[str]  # "ell" | "special_ed" | "gifted" | "mixed"
    assessment_type: Optional[str]     # "formative" | "summative" | "performance"

    # Component regeneration
    regenerate_component: Optional[str]  # "engagement" | "activities" | "assessments"
    num_suggestions: int = 3
```

### Component Regeneration

```python
async def regenerate_component(
    lesson: LessonPlan,
    component_name: str,  # Which component to regenerate
    constraints: Dict[str, Any],  # Duration, style, etc.
) -> LessonPhase | List[Assessment] | ...:
    """
    Regenerate single component, keeping others fixed.
    Returns multiple options (3-5 variations).
    """
```

### Optimization Suggestions

Suggestions generated by:
1. Analyze current lesson structure
2. Identify gaps (missing components, weak assessments)
3. Cross-reference with best practices
4. Generate specific, actionable suggestions
5. Prioritize by pedagogical impact

Example suggestions:
```python
[
    {
        "type": "activity_enhancement",
        "impact": "high",
        "suggestion": "Add peer discussion to practice phase",
        "rationale": "Improves retention through dialogue"
    },
    {
        "type": "cross_curricular",
        "impact": "medium",
        "suggestion": "Connect to Science standard NGSS.3-LS1-1",
        "rationale": "Standard overlaps with current objectives"
    }
]
```

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Duration adjustment | 1-5s | Quick DOM update |
| Style change (regenerate) | 10-20s | Qwen3 full regeneration |
| Component regeneration | 5-15s | Targeted Qwen3 call |
| Get 3-5 suggestions | 2-5s | Lightweight analysis |
| Export customized | <5s | Format conversion |

### Version Storage

Store in database:
```python
{
    lesson_id: "les_xyz123",
    version_number: 1,
    created_at: "2025-10-18T15:30:00Z",
    created_by: "teacher_email@school.edu",
    customizations: {...},
    status: "active" | "archived",
    notes: "ELL version with visual supports"
}
```

## Testing Strategy

### Unit Tests
- [ ] Customization schema validation
- [ ] Duration adjustment calculations
- [ ] Component isolation (regenerating one doesn't affect others)
- [ ] Suggestion generation logic

### Integration Tests
- [ ] End-to-end: customize → regenerate → export
- [ ] Version history: save, compare, restore
- [ ] Multi-style regeneration: each style produces different results
- [ ] Performance: meets <20s target for typical customization

### Acceptance Tests
- [ ] Teachers find customization interface intuitive
- [ ] Customized lessons are as usable as generated ones
- [ ] Version history doesn't slow down system
- [ ] Sharing works as expected
- [ ] Teachers report time savings with customization

## Related Capabilities

- **Lesson Plan Generation**: Generated lessons are starting point for customization
- **Multi-format Export**: Customized lessons exported with modifications intact
- **Teacher Dashboard**: Shows all saved and shared lessons

## Future Enhancements

- Batch customization (apply same changes to multiple lessons)
- AI-powered suggestions (ML model trained on teacher feedback)
- Collaborative editing (multiple teachers refine same lesson)
- Template creation (save customization as reusable template)
- Lesson plan analytics (track which customizations are most common)

## Constraints & Assumptions

### Constraints
- Version history limited to 10 versions to control storage
- Share links expire after 24 hours (security)
- Customization requests must complete within 60 seconds
- Component regeneration must maintain pedagogical consistency

### Assumptions
- Teachers understand basic lesson structure concepts
- Teachers have domain knowledge to evaluate customization quality
- Teachers want to keep control (not fully automated)
- Version history is "nice-to-have" not critical

## Version History

- **v1.0** (2025-10-18): Initial specification
