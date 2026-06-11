import { CustomSelect } from "@vkontakte/vkui";

export const QUESTION_TYPE_OPTIONS = [
  { label: "Свободный ответ", value: "TEXT" },
  { label: "Один вариант", value: "SINGLE_CHOICE" },
  { label: "Несколько вариантов", value: "MULTIPLE_CHOICE" },
  { label: "Выбор картинки", value: "IMAGE_CHOICE" },
  { label: "Загрузка картинки респондентом", value: "IMAGE_UPLOAD" },
  { label: "Рейтинг", value: "RATING" },
  { label: "Дата", value: "DATE" },
];

type Props = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function QuestionTypeSelect({ value, onChange, disabled }: Props) {
  return (
    <CustomSelect
      value={value}
      onChange={(_, newValue) => onChange(String(newValue ?? "TEXT"))}
      options={QUESTION_TYPE_OPTIONS}
      disabled={disabled}
    />
  );
}
