from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EmployeeIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=254)
    department: str = Field(min_length=2, max_length=100)
    job_title: str = Field(min_length=2, max_length=120)
    joining_date: date
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return value


class EmployeeOut(EmployeeIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = ""
    manager_id: int | None = None
    start_date: date
    end_date: date | None = None
    status: Literal["Planned", "In Progress", "On Hold", "Completed"] = "Planned"
    progress: int = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def dates_valid(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date")
        return self


class ProjectOut(ProjectIn):
    id: int
    manager_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class TaskIn(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = ""
    project_id: int
    employee_id: int | None = None
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    status: Literal["Open", "In Progress", "Blocked", "Completed"] = "Open"
    due_date: date | None = None


class TaskOut(TaskIn):
    id: int
    created_at: datetime
    project_name: str | None = None
    employee_name: str | None = None
    model_config = ConfigDict(from_attributes=True)
