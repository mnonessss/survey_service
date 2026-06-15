import uuid

import pytest
from fastapi import HTTPException

from app.models.enums import QuestionType
from app.models.question import Question
from app.schemas.public import AnswerSubmitItem
from app.services.answer_service import validate_answers_for_submit


def _question(qtype: QuestionType, *, required: bool = False) -> Question:
    q = Question()
    q.id = uuid.uuid4()
    q.question_type = qtype
    q.required = required
    return q


def test_text_answer_accepted():
    question = _question(QuestionType.TEXT, required=True)
    result = validate_answers_for_submit(
        [question],
        [AnswerSubmitItem(question_id=question.id, value_text="Ответ")],
        require_all_required=True,
    )
    assert question.id in result


def test_image_upload_requires_upload_path():
    question = _question(QuestionType.IMAGE_UPLOAD, required=True)
    with pytest.raises(HTTPException) as exc:
        validate_answers_for_submit(
            [question],
            [AnswerSubmitItem(question_id=question.id, value_text="not-a-path")],
            require_all_required=True,
        )
    assert exc.value.status_code == 400


def test_image_upload_multiple_requires_upload_paths():
    question = _question(QuestionType.IMAGE_UPLOAD_MULTIPLE, required=True)
    result = validate_answers_for_submit(
        [question],
        [
            AnswerSubmitItem(
                question_id=question.id,
                value_json=["/uploads/a.jpg", "/uploads/b.jpg"],
            ),
        ],
        require_all_required=True,
    )
    assert question.id in result


def test_single_choice_requires_exactly_one_option():
    question = _question(QuestionType.SINGLE_CHOICE, required=True)
    with pytest.raises(HTTPException) as exc:
        validate_answers_for_submit(
            [question],
            [AnswerSubmitItem(question_id=question.id, value_json=["a", "b"])],
            require_all_required=True,
        )
    assert "exactly one" in exc.value.detail.lower()


def test_missing_required_answer_rejected():
    question = _question(QuestionType.TEXT, required=True)
    with pytest.raises(HTTPException) as exc:
        validate_answers_for_submit([question], [], require_all_required=True)
    assert "missing required" in exc.value.detail.lower()
