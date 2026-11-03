from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import Employee, Project, Task
from .schemas import EmployeeIn, EmployeeOut, ProjectIn, TaskIn

app = FastAPI(title="WorkSphere API", version="1.0.0", description="Employee, project, and task management API")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def initialize_schema():
    # Creates only WorkSphere's own tables; use migrations for production schema changes.
    Base.metadata.create_all(bind=engine)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_, exc):
    return __import__("fastapi").responses.JSONResponse(status_code=503, content={"detail": "Database unavailable or operation could not be completed"})


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "worksphere-api"}


def paged(query, db, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_or_404(db, model, ident):
    row = db.get(model, ident)
    if row is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return row


@app.get("/api/employees")
def employees(db: Session = Depends(get_db), search: str = "", department: str = "", sort_by: str = "full_name", order: str = "asc", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = select(Employee)
    if search: q = q.where(or_(Employee.full_name.ilike(f"%{search}%"), Employee.email.ilike(f"%{search}%")))
    if department: q = q.where(Employee.department == department)
    column = getattr(Employee, sort_by, Employee.full_name)
    q = q.order_by(column.desc() if order.lower() == "desc" else column.asc())
    return paged(q, db, page, page_size)


@app.get("/api/employees/{employee_id}", response_model=EmployeeOut)
def employee(employee_id: int, db: Session = Depends(get_db)): return get_or_404(db, Employee, employee_id)


@app.post("/api/employees", response_model=EmployeeOut, status_code=201)
def create_employee(data: EmployeeIn, db: Session = Depends(get_db)):
    row = Employee(**data.model_dump()); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError: db.rollback(); raise HTTPException(409, "An employee with this email already exists")
    return row


@app.put("/api/employees/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, data: EmployeeIn, db: Session = Depends(get_db)):
    row = get_or_404(db, Employee, employee_id)
    for key, value in data.model_dump().items(): setattr(row, key, value)
    try: db.commit(); db.refresh(row)
    except IntegrityError: db.rollback(); raise HTTPException(409, "An employee with this email already exists")
    return row


@app.delete("/api/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Employee, employee_id)); db.commit()


@app.get("/api/projects")
def projects(db: Session = Depends(get_db), search: str = "", status: str = "", sort_by: str = "start_date", order: str = "desc", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = select(Project)
    if search: q = q.where(Project.name.ilike(f"%{search}%"))
    if status: q = q.where(Project.status == status)
    col = getattr(Project, sort_by, Project.start_date); q = q.order_by(col.desc() if order.lower() == "desc" else col.asc())
    rows = paged(q, db, page, page_size)
    for p in rows["items"]: p.manager_name = p.manager.full_name if p.manager else None
    return rows


@app.get("/api/projects/{project_id}")
def project(project_id: int, db: Session = Depends(get_db)):
    p = get_or_404(db, Project, project_id); p.manager_name = p.manager.full_name if p.manager else None; return p


@app.post("/api/projects", status_code=201)
def create_project(data: ProjectIn, db: Session = Depends(get_db)):
    values = data.model_dump()
    if values["manager_id"] and not db.get(Employee, values["manager_id"]): raise HTTPException(400, "Project manager does not exist")
    row = Project(**values); db.add(row); db.commit(); db.refresh(row); row.manager_name = row.manager.full_name if row.manager else None; return row


@app.put("/api/projects/{project_id}")
def update_project(project_id: int, data: ProjectIn, db: Session = Depends(get_db)):
    row = get_or_404(db, Project, project_id); values = data.model_dump()
    if values["manager_id"] and not db.get(Employee, values["manager_id"]): raise HTTPException(400, "Project manager does not exist")
    for k, v in values.items(): setattr(row, k, v)
    db.commit(); db.refresh(row); row.manager_name = row.manager.full_name if row.manager else None; return row


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)): db.delete(get_or_404(db, Project, project_id)); db.commit()


@app.get("/api/tasks")
def tasks(db: Session = Depends(get_db), search: str = "", status: str = "", priority: str = "", project_id: int | None = None, employee_id: int | None = None, sort_by: str = "created_at", order: str = "desc", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = select(Task)
    if search: q = q.where(Task.title.ilike(f"%{search}%"))
    if status: q = q.where(Task.status == status)
    if priority: q = q.where(Task.priority == priority)
    if project_id: q = q.where(Task.project_id == project_id)
    if employee_id: q = q.where(Task.employee_id == employee_id)
    col = getattr(Task, sort_by, Task.created_at); q = q.order_by(col.desc() if order.lower() == "desc" else col.asc())
    rows = paged(q, db, page, page_size)
    for t in rows["items"]: t.project_name = t.project.name; t.employee_name = t.assignee.full_name if t.assignee else None
    return rows


@app.get("/api/tasks/{task_id}")
def task(task_id: int, db: Session = Depends(get_db)):
    t = get_or_404(db, Task, task_id); t.project_name = t.project.name; t.employee_name = t.assignee.full_name if t.assignee else None; return t


def validate_task_refs(db, data):
    if not db.get(Project, data.project_id): raise HTTPException(400, "Project does not exist")
    if data.employee_id and not db.get(Employee, data.employee_id): raise HTTPException(400, "Assigned employee does not exist")


@app.post("/api/tasks", status_code=201)
def create_task(data: TaskIn, db: Session = Depends(get_db)):
    validate_task_refs(db, data); t = Task(**data.model_dump()); db.add(t); db.commit(); db.refresh(t); t.project_name = t.project.name; t.employee_name = t.assignee.full_name if t.assignee else None; return t


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, data: TaskIn, db: Session = Depends(get_db)):
    t = get_or_404(db, Task, task_id); validate_task_refs(db, data)
    for k, v in data.model_dump().items(): setattr(t, k, v)
    db.commit(); db.refresh(t); t.project_name = t.project.name; t.employee_name = t.assignee.full_name if t.assignee else None; return t


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)): db.delete(get_or_404(db, Task, task_id)); db.commit()


@app.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    count = lambda model, *conditions: db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
    statuses = ["Open", "In Progress", "Blocked", "Completed"]
    grouped = {s: count(Task, Task.status == s) for s in statuses}
    return {"total_employees": count(Employee), "total_projects": count(Project), "active_projects": count(Project, Project.status == "In Progress"), "open_tasks": count(Task, Task.status.in_(["Open", "In Progress", "Blocked"])), "completed_tasks": grouped["Completed"], "tasks_by_status": grouped}


@app.get("/api/dashboard/recent-activity")
def recent_activity(db: Session = Depends(get_db), limit: int = Query(8, ge=1, le=30)):
    projects = db.scalars(select(Project).order_by(Project.id.desc()).limit(limit)).all()
    tasks = db.scalars(select(Task).order_by(Task.created_at.desc()).limit(limit)).all()
    for p in projects: p.manager_name = p.manager.full_name if p.manager else None
    for t in tasks: t.project_name = t.project.name; t.employee_name = t.assignee.full_name if t.assignee else None
    return {"recent_projects": projects, "recent_tasks": tasks}
