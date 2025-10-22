import pytest
from pydantic import ValidationError

from src.jina_rag_pipeline.api.models import UpdateLessonRequest
from src.jina_rag_pipeline.models.educational import VALID_TEACHING_STYLES


class TestUpdateLessonRequest:
    
    def test_empty_request_valid(self):
        """All fields optional - empty request should be valid."""
        request = UpdateLessonRequest()
        assert request.markdown_content is None
        assert request.title is None
        assert request.duration_minutes is None
        assert request.teaching_style is None
        assert request.learning_objective is None
    
    def test_partial_update_title_only(self):
        """Partial update with only title field."""
        request = UpdateLessonRequest(title="New Title")
        assert request.title == "New Title"
        assert request.markdown_content is None
        assert request.duration_minutes is None
    
    def test_partial_update_multiple_fields(self):
        """Partial update with multiple fields."""
        request = UpdateLessonRequest(
            title="Updated Title",
            duration_minutes=45,
            teaching_style="inquiry"
        )
        assert request.title == "Updated Title"
        assert request.duration_minutes == 45
        assert request.teaching_style == "inquiry"
        assert request.markdown_content is None
        assert request.learning_objective is None
    
    def test_all_fields_provided(self):
        """Full update with all fields."""
        request = UpdateLessonRequest(
            markdown_content="# New Content\n\nUpdated lesson.",
            title="Complete Update",
            duration_minutes=60,
            teaching_style="project",
            learning_objective="Students will understand new concepts"
        )
        assert request.markdown_content == "# New Content\n\nUpdated lesson."
        assert request.title == "Complete Update"
        assert request.duration_minutes == 60
        assert request.teaching_style == "project"
        assert request.learning_objective == "Students will understand new concepts"
    
    def test_title_empty_string_invalid(self):
        """Title with empty string should fail min_length validation."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(title="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)
    
    def test_title_too_long_invalid(self):
        """Title exceeding 500 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(title="x" * 501)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)
    
    def test_title_max_length_valid(self):
        """Title at exactly 500 characters should be valid."""
        request = UpdateLessonRequest(title="x" * 500)
        assert len(request.title) == 500
    
    def test_markdown_content_empty_string_invalid(self):
        """Markdown content with empty string should fail min_length validation."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(markdown_content="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("markdown_content",) for e in errors)
    
    def test_markdown_content_too_long_invalid(self):
        """Markdown content exceeding 100000 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(markdown_content="x" * 100001)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("markdown_content",) for e in errors)
    
    def test_markdown_content_max_length_valid(self):
        """Markdown content at exactly 100000 characters should be valid."""
        request = UpdateLessonRequest(markdown_content="x" * 100000)
        assert len(request.markdown_content) == 100000
    
    def test_learning_objective_empty_string_invalid(self):
        """Learning objective with empty string should fail min_length validation."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(learning_objective="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("learning_objective",) for e in errors)
    
    def test_learning_objective_too_long_invalid(self):
        """Learning objective exceeding 500 characters should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(learning_objective="x" * 501)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("learning_objective",) for e in errors)
    
    def test_learning_objective_max_length_valid(self):
        """Learning objective at exactly 500 characters should be valid."""
        request = UpdateLessonRequest(learning_objective="x" * 500)
        assert len(request.learning_objective) == 500
    
    def test_duration_minutes_below_minimum_invalid(self):
        """Duration below 20 minutes should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(duration_minutes=19)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("duration_minutes",) for e in errors)
    
    def test_duration_minutes_above_maximum_invalid(self):
        """Duration above 90 minutes should fail."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(duration_minutes=91)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("duration_minutes",) for e in errors)
    
    def test_duration_minutes_minimum_valid(self):
        """Duration at exactly 20 minutes should be valid."""
        request = UpdateLessonRequest(duration_minutes=20)
        assert request.duration_minutes == 20
    
    def test_duration_minutes_maximum_valid(self):
        """Duration at exactly 90 minutes should be valid."""
        request = UpdateLessonRequest(duration_minutes=90)
        assert request.duration_minutes == 90
    
    def test_duration_minutes_mid_range_valid(self):
        """Duration in middle of range should be valid."""
        request = UpdateLessonRequest(duration_minutes=45)
        assert request.duration_minutes == 45
    
    def test_teaching_style_valid_balanced(self):
        """Teaching style 'balanced' should be valid."""
        request = UpdateLessonRequest(teaching_style="balanced")
        assert request.teaching_style == "balanced"
    
    def test_teaching_style_valid_direct(self):
        """Teaching style 'direct' should be valid."""
        request = UpdateLessonRequest(teaching_style="direct")
        assert request.teaching_style == "direct"
    
    def test_teaching_style_valid_inquiry(self):
        """Teaching style 'inquiry' should be valid."""
        request = UpdateLessonRequest(teaching_style="inquiry")
        assert request.teaching_style == "inquiry"
    
    def test_teaching_style_valid_project(self):
        """Teaching style 'project' should be valid."""
        request = UpdateLessonRequest(teaching_style="project")
        assert request.teaching_style == "project"
    
    def test_teaching_style_invalid(self):
        """Invalid teaching style should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(teaching_style="invalid_style")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("teaching_style",) for e in errors)
        error_msg = str(exc_info.value)
        assert "Invalid teaching style" in error_msg
    
    def test_teaching_style_case_sensitive(self):
        """Teaching style validation should be case-sensitive."""
        with pytest.raises(ValidationError):
            UpdateLessonRequest(teaching_style="BALANCED")
    
    def test_all_teaching_styles_documented_valid(self):
        """All documented teaching styles should be valid."""
        for style in VALID_TEACHING_STYLES:
            request = UpdateLessonRequest(teaching_style=style)
            assert request.teaching_style == style
    
    def test_model_dump_exclude_unset(self):
        """Using model_dump with exclude_unset should only include set fields."""
        request = UpdateLessonRequest(title="Test", duration_minutes=45)
        dumped = request.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "duration_minutes" in dumped
        assert "markdown_content" not in dumped
        assert "teaching_style" not in dumped
        assert "learning_objective" not in dumped
    
    def test_model_dump_exclude_unset_empty(self):
        """Empty request with exclude_unset should produce empty dict."""
        request = UpdateLessonRequest()
        dumped = request.model_dump(exclude_unset=True)
        assert dumped == {}
    
    def test_validation_error_messages_helpful(self):
        """Validation errors should provide helpful messages."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateLessonRequest(title="", duration_minutes=15, teaching_style="wrong")
        
        error_msg = str(exc_info.value)
        assert "title" in error_msg.lower() or "string" in error_msg.lower()
