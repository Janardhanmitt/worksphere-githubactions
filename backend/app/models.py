from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (Index("ix_employees_name", "full_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_name", "name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Planned", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manager: Mapped[Employee | None] = relationship()
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_status_due", "status", "due_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Open", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[Employee | None] = relationship(back_populates="tasks")
