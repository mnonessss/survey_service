import uuid

from app.models.enums import QuestionType
from app.models.question import Question
from app.services.response_display import format_export_value


def _question(qtype: QuestionType) -> Question:
    q = Question()
    q.id = uuid.uuid4()
    q.question_type = qtype
    q.options = []
    return q


def test_export_single_image_upload_uses_full_url():
    value = format_export_value(
        _question(QuestionType.IMAGE_UPLOAD),
        value_text="/uploads/responses/abc/photo.jpg",
        value_json=None,
    )
    assert value == "http://testserver/uploads/responses/abc/photo.jpg"


def test_export_multiple_image_upload_joins_urls():
    value = format_export_value(
        _question(QuestionType.IMAGE_UPLOAD_MULTIPLE),
        value_text=None,
        value_json=[
            "/uploads/responses/a/1.jpg",
            "/uploads/responses/a/2.jpg",
        ],
    )
    assert "http://testserver/uploads/responses/a/1.jpg" in value
    assert "http://testserver/uploads/responses/a/2.jpg" in value
    assert ", " in value


def test_export_text_answer_is_escaped():
    value = format_export_value(
        _question(QuestionType.TEXT),
        value_text="hello & <world>",
        value_json=None,
    )
    assert value == "hello & <world>"
