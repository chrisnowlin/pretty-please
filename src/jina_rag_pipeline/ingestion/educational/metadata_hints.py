"""Best-effort metadata extraction from educational content."""

import re
from typing import Dict, Optional, List


# Grade level patterns (case-insensitive)
GRADE_PATTERNS = {
    "PreK": [
        r"\bpre-?k\b", r"\bpre-?kindergarten\b", r"\bpreschool\b"
    ],
    "K": [
        r"\bkindergarten\b", r"grade\s*k", r"gradek"
    ],
    "1": [r"grade\s*1", r"grade1", r"\bfirst grade\b", r"\b1st grade\b"],
    "2": [r"grade\s*2", r"grade2", r"\bsecond grade\b", r"\b2nd grade\b"],
    "3": [r"grade\s*3", r"grade3", r"\bthird grade\b", r"\b3rd grade\b"],
    "4": [r"grade\s*4", r"grade4", r"\bfourth grade\b", r"\b4th grade\b"],
    "5": [r"grade\s*5", r"grade5", r"\bfifth grade\b", r"\b5th grade\b"],
    "6": [r"grade\s*6", r"grade6", r"\bsixth grade\b", r"\b6th grade\b"],
    "7": [r"grade\s*7", r"grade7", r"\bseventh grade\b", r"\b7th grade\b"],
    "8": [r"grade\s*8", r"grade8", r"\beighth grade\b", r"\b8th grade\b"],
    "9": [r"grade\s*9", r"grade9", r"\bninth grade\b", r"\b9th grade\b", r"\bfreshman\b"],
    "10": [r"grade\s*10", r"grade10", r"\btenth grade\b", r"\b10th grade\b", r"\bsophomore\b"],
    "11": [r"grade\s*11", r"grade11", r"\beleventh grade\b", r"\b11th grade\b", r"\bjunior\b"],
    "12": [r"grade\s*12", r"grade12", r"\btwelfth grade\b", r"\b12th grade\b", r"\bsenior\b"],

    # Ranges
    "K-2": [r"\bk-2\b", r"\bearly elementary\b", r"grades\s*k-2"],
    "3-5": [r"\b3-5\b", r"\bupper elementary\b", r"grades\s*3-5"],
    "6-8": [r"\b6-8\b", r"\bmiddle school\b", r"grades\s*6-8"],
    "9-12": [r"\b9-12\b", r"\bhigh school\b", r"grades\s*9-12", r"\bsecondary\b"],

    "College": [r"\bcollege\b", r"\buniversity\b", r"\bundergraduate\b", r"\bpost-secondary\b"],
}

# Subject patterns (case-insensitive)
# Note: Patterns without strict word boundaries to work with filenames like "Grade5_Science"
SUBJECT_PATTERNS = {
    "Mathematics": [
        r"math(?:ematics)?", r"algebra", r"geometry",
        r"calculus", r"trigonometry", r"arithmetic", r"statistics"
    ],
    "Science": [
        r"science", r"physics", r"chemistry", r"biology",
        r"earth science", r"environmental science", r"astronomy"
    ],
    "English Language Arts": [
        r"\bela\b", r"english", r"reading", r"writing",
        r"literature", r"grammar", r"composition", r"language arts"
    ],
    "Social Studies": [
        r"social studies", r"history", r"geography", r"civics",
        r"government", r"economics", r"world history", r"us history"
    ],
    "Arts & Design": [
        r"\bart\b", r"music", r"drama", r"theatre",
        r"visual art", r"performing arts", r"design"
    ],
    "Physical Education": [
        r"\bpe\b", r"physical education", r"health", r"fitness",
        r"athletics", r"sports"
    ],
    "World Languages": [
        r"spanish", r"french", r"italian", r"german",
        r"foreign language", r"world language", r"mandarin"
    ],
    "Technology": [
        r"computer science", r"technology", r"coding",
        r"programming", r"digital literacy", r"\bit\b"
    ],
    "Career & Technical Education": [
        r"\bcte\b", r"career", r"vocational", r"technical education",
        r"trade"
    ],
}


def extract_grade_level(text: str) -> Optional[str]:
    """
    Extract grade level from text using pattern matching.

    Args:
        text: Text to analyze

    Returns:
        Detected grade level (abbreviated format) or None
    """
    text_lower = text.lower()

    # Check each grade pattern
    for grade, patterns in GRADE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return grade

    return None


def extract_subject(text: str) -> Optional[str]:
    """
    Extract subject area from text using pattern matching.

    Args:
        text: Text to analyze

    Returns:
        Detected subject or None
    """
    text_lower = text.lower()

    # Check each subject pattern
    for subject, patterns in SUBJECT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return subject

    return None


def extract_all_possible_subjects(text: str) -> List[str]:
    """
    Extract all possible subjects mentioned in text.

    Args:
        text: Text to analyze

    Returns:
        List of detected subjects
    """
    text_lower = text.lower()
    found_subjects = []

    for subject, patterns in SUBJECT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                if subject not in found_subjects:
                    found_subjects.append(subject)
                break  # Move to next subject once one pattern matches

    return found_subjects


def extract_metadata_hints(
    text: str,
    filename: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Extract educational metadata hints from text and filename.

    This is a best-effort extraction that returns None for fields
    that cannot be detected. System should work fine without metadata.

    Args:
        text: Content text to analyze
        filename: Optional filename to analyze

    Returns:
        Dictionary with detected metadata:
        {
            "grade": str or None,
            "subject": str or None,
            "content_type": "educational" if any hints found, None otherwise
        }
    """
    # Combine text and filename for analysis
    combined_text = text
    if filename:
        combined_text = f"{filename} {text}"

    grade = extract_grade_level(combined_text)
    subject = extract_subject(combined_text)

    # Determine if this looks like educational content
    content_type = "educational" if (grade or subject) else None

    return {
        "grade": grade,
        "subject": subject,
        "content_type": content_type,
    }


def enrich_chunk_metadata(
    existing_metadata: Dict,
    text: str,
    filename: Optional[str] = None
) -> Dict:
    """
    Add educational metadata hints to existing chunk metadata.

    Args:
        existing_metadata: Existing metadata dict from ingestion
        text: Chunk text content
        filename: Optional source filename

    Returns:
        Enriched metadata dict (original + educational hints)
    """
    hints = extract_metadata_hints(text, filename)

    # Only add non-None hints
    enriched = existing_metadata.copy()
    for key, value in hints.items():
        if value is not None:
            enriched[f"edu_{key}"] = value

    return enriched


def matches_grade(material_grade: str, query_grade: str) -> bool:
    """
    Check if material grade matches query grade (handles ranges).

    Args:
        material_grade: Grade from material metadata (e.g., "3", "3-5")
        query_grade: Grade from query (e.g., "4", "6-8")

    Returns:
        True if grades match or overlap
    """
    # Exact match
    if material_grade == query_grade:
        return True

    # Parse ranges
    def parse_range(grade_str: str) -> List[int]:
        """Parse grade string into list of grade numbers."""
        if "-" in grade_str:
            # Range like "3-5"
            start, end = grade_str.split("-")
            # Handle K-2 specially
            if start.upper() == "K":
                start_num = 0
            else:
                start_num = int(start)

            end_num = int(end)
            return list(range(start_num, end_num + 1))
        elif grade_str.upper() == "K":
            return [0]
        elif grade_str == "PreK":
            return [-1]
        elif grade_str == "College":
            return [13]  # Treat college as grade 13
        else:
            # Single grade number
            return [int(grade_str)]

    try:
        material_grades = parse_range(material_grade)
        query_grades = parse_range(query_grade)

        # Check if any overlap
        return bool(set(material_grades) & set(query_grades))
    except (ValueError, AttributeError):
        # If parsing fails, be permissive
        return True


def matches_subject(material_subject: str, query_subject: str) -> bool:
    """
    Check if material subject matches query subject.

    Args:
        material_subject: Subject from material metadata
        query_subject: Subject from query

    Returns:
        True if subjects match (case-insensitive)
    """
    return material_subject.lower() == query_subject.lower()
