from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator


class Top100QueryParams(BaseModel):
    sort_by: str = Field(
        "stars",
        description="Поле для сортировки (stars, watchers, forks, open_issues, language)",
        example="stars"
    )
    order: str = Field(
        "desc",
        description="Порядок сортировки (asc или desc)",
        example="desc"
    )

    @field_validator("sort_by")
    def validate_sort_by(cls, value):
        valid_sort_fields = ["stars", "watchers", "forks", "open_issues", "language"]
        if value not in valid_sort_fields:
            message = (
                f"Недопустимое поле для сортировки: {value}. "
                f"Допустимые значения: {', '.join(valid_sort_fields)}"
            )
            raise HTTPException(status_code=422, detail=message)
        return value

    @field_validator("order")
    def validate_order(cls, value):
        valid_order_values = ["asc", "desc"]
        if value not in valid_order_values:
            message = (
                f"Недопустимый порядок сортировки: {value}. "
                f"Допустимые значения: {', '.join(valid_order_values)}"
            )
            raise HTTPException(status_code=422, detail=message)
        return value
