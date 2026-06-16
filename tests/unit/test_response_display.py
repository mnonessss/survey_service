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


def test_export_single_image_upload_uses_label_not_url():
    value = format_export_value(
        _question(QuestionType.IMAGE_UPLOAD),
        value_text="/uploads/responses/abc/photo.jpg",
        value_json=None,
    )
    assert value == "1 изображение (см. в личном кабинете)"
    assert "http" not in value
    assert "/uploads/" not in value


def test_export_multiple_image_upload_uses_count_label():
    value = format_export_value(
        _question(QuestionType.IMAGE_UPLOAD_MULTIPLE),
        value_text=None,
        value_json=[
            "/uploads/responses/a/1.jpg",
            "/uploads/responses/a/2.jpg",
        ],
    )
    assert value == "2 изображения (см. в личном кабинете)"
    assert "http" not in value


def test_export_text_answer_is_escaped():
    value = format_export_value(
        _question(QuestionType.TEXT),
        value_text="hello & <world>",
        value_json=None,
    )
    assert value == "hello & <world>"
