import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.jina_rag_pipeline.api.app import create_app
from src.jina_rag_pipeline.database.models import Base, Lesson
from src.jina_rag_pipeline.database import get_db


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database."""
    app = create_app()
    
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_lesson(test_db):
    """Create a sample lesson in the database."""
    db = test_db()
    lesson = Lesson(
        lesson_id="test-lesson-123",
        title="Introduction to Fractions",
        markdown_content="# Fractions\n\nThis is a lesson about fractions.",
        grade="Grade 3",
        subject="Mathematics",
        topic="Fractions - Basic Concepts",
        learning_objective="Students will understand basic fraction concepts",
        duration_minutes=45,
        teaching_style="balanced",
        metadata_json={"tags": ["math", "fractions"]},
        sources_count=5,
        images_count=2,
        is_favorite=False
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    db.close()
    return lesson


class TestUpdateLessonEndpoint:
    """Integration tests for PATCH /api/lessons/{lesson_id} endpoint."""
    
    def test_update_title_only(self, client, sample_lesson):
        """Update only the title field."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "Updated Fractions Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Fractions Title"
        assert data["markdown_content"] == sample_lesson.markdown_content
        assert data["duration_minutes"] == sample_lesson.duration_minutes
        assert data["teaching_style"] == sample_lesson.teaching_style
        assert data["learning_objective"] == sample_lesson.learning_objective
    
    def test_update_markdown_content_only(self, client, sample_lesson):
        """Update only the markdown content field."""
        new_content = "# Updated Content\n\nThis is the updated lesson content."
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"markdown_content": new_content}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["markdown_content"] == new_content
        assert data["title"] == sample_lesson.title
    
    def test_update_duration_minutes_only(self, client, sample_lesson):
        """Update only the duration field."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"duration_minutes": 60}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 60
        assert data["title"] == sample_lesson.title
    
    def test_update_teaching_style_only(self, client, sample_lesson):
        """Update only the teaching style field."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"teaching_style": "inquiry"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["teaching_style"] == "inquiry"
        assert data["title"] == sample_lesson.title
    
    def test_update_learning_objective_only(self, client, sample_lesson):
        """Update only the learning objective field."""
        new_objective = "Students will master advanced fraction operations"
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"learning_objective": new_objective}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["learning_objective"] == new_objective
        assert data["title"] == sample_lesson.title
    
    def test_update_multiple_fields(self, client, sample_lesson):
        """Update multiple fields at once."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={
                "title": "Advanced Fractions",
                "duration_minutes": 70,
                "teaching_style": "project",
                "learning_objective": "Students will solve complex fraction problems"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Advanced Fractions"
        assert data["duration_minutes"] == 70
        assert data["teaching_style"] == "project"
        assert data["learning_objective"] == "Students will solve complex fraction problems"
        assert data["markdown_content"] == sample_lesson.markdown_content
    
    def test_update_all_editable_fields(self, client, sample_lesson):
        """Update all editable fields."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={
                "markdown_content": "# Complete Rewrite\n\nBrand new content.",
                "title": "Completely New Title",
                "duration_minutes": 90,
                "teaching_style": "direct",
                "learning_objective": "Completely new objective"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["markdown_content"] == "# Complete Rewrite\n\nBrand new content."
        assert data["title"] == "Completely New Title"
        assert data["duration_minutes"] == 90
        assert data["teaching_style"] == "direct"
        assert data["learning_objective"] == "Completely new objective"
    
    def test_non_editable_fields_unchanged(self, client, sample_lesson):
        """Verify non-editable fields remain unchanged after update."""
        original_grade = sample_lesson.grade
        original_subject = sample_lesson.subject
        original_topic = sample_lesson.topic
        original_sources = sample_lesson.sources_count
        original_images = sample_lesson.images_count
        original_created = sample_lesson.created_at
        
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "New Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["grade"] == original_grade
        assert data["subject"] == original_subject
        assert data["topic"] == original_topic
        assert data["sources_count"] == original_sources
        assert data["images_count"] == original_images
    
    def test_updated_at_timestamp_changes(self, client, sample_lesson):
        """Verify updated_at timestamp is updated."""
        original_updated = sample_lesson.updated_at
        
        import time
        time.sleep(0.1)
        
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        assert updated_at != original_updated
    
    def test_created_at_timestamp_unchanged(self, client, sample_lesson):
        """Verify created_at timestamp remains unchanged."""
        original_created = sample_lesson.created_at.isoformat()
        
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created_at"] == original_created
    
    def test_lesson_not_found_returns_404(self, client):
        """Test 404 error for non-existent lesson ID."""
        response = client.patch(
            "/api/lessons/99999",
            json={"title": "Some Title"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_empty_request_body_returns_400(self, client, sample_lesson):
        """Test 400 error when no fields are provided."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={}
        )
        
        assert response.status_code == 400
        assert "no fields" in response.json()["detail"].lower()
    
    def test_title_empty_string_returns_422(self, client, sample_lesson):
        """Test validation error for empty title."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": ""}
        )
        
        assert response.status_code == 422
    
    def test_title_too_long_returns_422(self, client, sample_lesson):
        """Test validation error for title exceeding max length."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "x" * 501}
        )
        
        assert response.status_code == 422
    
    def test_markdown_content_empty_string_returns_422(self, client, sample_lesson):
        """Test validation error for empty markdown content."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"markdown_content": ""}
        )
        
        assert response.status_code == 422
    
    def test_markdown_content_too_long_returns_422(self, client, sample_lesson):
        """Test validation error for markdown content exceeding max length."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"markdown_content": "x" * 100001}
        )
        
        assert response.status_code == 422
    
    def test_duration_below_minimum_returns_422(self, client, sample_lesson):
        """Test validation error for duration below 20 minutes."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"duration_minutes": 19}
        )
        
        assert response.status_code == 422
    
    def test_duration_above_maximum_returns_422(self, client, sample_lesson):
        """Test validation error for duration above 90 minutes."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"duration_minutes": 91}
        )
        
        assert response.status_code == 422
    
    def test_invalid_teaching_style_returns_422(self, client, sample_lesson):
        """Test validation error for invalid teaching style."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"teaching_style": "invalid_style"}
        )
        
        assert response.status_code == 422
        assert "teaching style" in response.json()["detail"][0]["msg"].lower()
    
    def test_learning_objective_empty_string_returns_422(self, client, sample_lesson):
        """Test validation error for empty learning objective."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"learning_objective": ""}
        )
        
        assert response.status_code == 422
    
    def test_learning_objective_too_long_returns_422(self, client, sample_lesson):
        """Test validation error for learning objective exceeding max length."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"learning_objective": "x" * 501}
        )
        
        assert response.status_code == 422
    
    def test_response_includes_all_fields(self, client, sample_lesson):
        """Verify response includes all lesson fields."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "Test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "id", "lesson_id", "title", "markdown_content", "grade", "subject",
            "topic", "learning_objective", "duration_minutes", "teaching_style",
            "sources_count", "images_count", "is_favorite", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_database_persistence(self, client, sample_lesson, test_db):
        """Verify changes are persisted to database."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "Persisted Title", "duration_minutes": 75}
        )
        
        assert response.status_code == 200
        
        db = test_db()
        lesson = db.query(Lesson).filter(Lesson.id == sample_lesson.id).first()
        assert lesson.title == "Persisted Title"
        assert lesson.duration_minutes == 75
        db.close()
    
    def test_multiple_updates_sequential(self, client, sample_lesson):
        """Test multiple sequential updates to same lesson."""
        response1 = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"title": "First Update"}
        )
        assert response1.status_code == 200
        
        response2 = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"duration_minutes": 80}
        )
        assert response2.status_code == 200
        
        response3 = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"teaching_style": "project"}
        )
        assert response3.status_code == 200
        
        data = response3.json()
        assert data["title"] == "First Update"
        assert data["duration_minutes"] == 80
        assert data["teaching_style"] == "project"
    
    def test_all_valid_teaching_styles(self, client, sample_lesson):
        """Test all valid teaching styles can be set."""
        teaching_styles = ["balanced", "direct", "inquiry", "project"]
        
        for style in teaching_styles:
            response = client.patch(
                f"/api/lessons/{sample_lesson.id}",
                json={"teaching_style": style}
            )
            assert response.status_code == 200
            assert response.json()["teaching_style"] == style
    
    @pytest.mark.integration
    def test_boundary_values(self, client, sample_lesson):
        """Test boundary values for numeric and string fields."""
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={
                "title": "x" * 500,
                "markdown_content": "y" * 100000,
                "learning_objective": "z" * 500,
                "duration_minutes": 20
            }
        )
        assert response.status_code == 200
        
        response = client.patch(
            f"/api/lessons/{sample_lesson.id}",
            json={"duration_minutes": 90}
        )
        assert response.status_code == 200
