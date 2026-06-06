import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class SurveyStatus(enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"


class QuestionType(enum.Enum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TEXT = "TEXT"
    IMAGE_CHOICE = "IMAGE_CHOICE"
    RATING = "RATING"
    DATE = "DATE"
    IMAGE_UPLOAD = "IMAGE_UPLOAD"
