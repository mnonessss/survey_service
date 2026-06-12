export function questionHint(type: string): string {
  switch (type) {
    case "TEXT":
      return "Введите произвольный текстовый ответ.";
    case "SINGLE_CHOICE":
      return "Выберите один вариант из списка.";
    case "MULTIPLE_CHOICE":
      return "Можно выбрать несколько вариантов.";
    case "IMAGE_CHOICE":
      return "Выберите одну картинку из предложенных.";
    case "IMAGE_UPLOAD":
      return "Прикрепите одно изображение (JPEG, PNG, GIF или WebP, до 5 МБ).";
    case "IMAGE_UPLOAD_MULTIPLE":
      return "Можно прикрепить несколько изображений (JPEG, PNG, GIF или WebP, до 5 МБ каждое).";
    case "RATING":
      return "Оцените по шкале от 1 до 10, где 10 — наивысшая оценка.";
    case "DATE":
      return "Выберите дату в календаре.";
    default:
      return "";
  }
}

export function questionTypeLabel(type: string): string {
  switch (type) {
    case "TEXT":
      return "Свободный ответ";
    case "SINGLE_CHOICE":
      return "Один вариант";
    case "MULTIPLE_CHOICE":
      return "Несколько вариантов";
    case "IMAGE_CHOICE":
      return "Выбор картинки";
    case "IMAGE_UPLOAD":
      return "Одна картинка";
    case "IMAGE_UPLOAD_MULTIPLE":
      return "Несколько картинок";
    case "RATING":
      return "Рейтинг";
    case "DATE":
      return "Дата";
    default:
      return type;
  }
}
