from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import psycopg2  # <--- 新增：用于连接 PostgreSQL
from contextlib import contextmanager  # <--- 新增：用于简化连接管理

app = FastAPI()

# 静态文件 & 模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 从环境变量获取数据库连接URL (Render 会自动注入)
DATABASE_URL = os.environ.get("DATABASE_URL")


# 【新函数】上下文管理器，用于自动获取连接和安全关闭
@contextmanager
def get_db_conn():
    if not DATABASE_URL:
        # 如果在云端，但没有 DATABASE_URL，则抛出错误
        raise Exception("DATABASE_URL is not set! Cannot connect to PostgreSQL.")

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    finally:
        # 确保连接在退出 with 块时关闭
        if conn:
            conn.close()


# 【新函数】初始化数据库：创建表
def init_db():
    try:
        with get_db_conn() as conn:
            c = conn.cursor()
            # PostgreSQL 使用 SERIAL PRIMARY KEY 实现自增 ID
            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error during DB initialization (PostgreSQL): {e}")


@app.on_event("startup")
def startup_event():
    # 确保在应用启动时创建表
    init_db()


# 获取任务（自动重新编号）
def get_tasks():
    # 使用 with 语句自动管理连接
    with get_db_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id, content FROM tasks ORDER BY id")
        rows = c.fetchall()

    # 重新编号序号（index 从 1 开始）
    return [{"seq": i + 1, "id": row[0], "content": row[1]} for i, row in enumerate(rows)]


@app.get("/")
def read_root(request: Request):
    tasks = get_tasks()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})


@app.post("/add")
def add_task(content: str = Form(...)):
    with get_db_conn() as conn:
        c = conn.cursor()
        # PostgreSQL 使用 %s 作为参数占位符
        c.execute("INSERT INTO tasks (content) VALUES (%s)", (content,))
        conn.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{task_id}")
def delete_task(task_id: int):
    with get_db_conn() as conn:
        c = conn.cursor()
        # PostgreSQL 使用 %s 作为参数占位符
        c.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/update/{task_id}")
def update_task(task_id: int, content: str = Form(...)):
    with get_db_conn() as conn:
        c = conn.cursor()
        # PostgreSQL 使用 %s 作为参数占位符
        c.execute("UPDATE tasks SET content = %s WHERE id = %s", (content, task_id))
        conn.commit()
    return RedirectResponse(url="/", status_code=303)


# 🔍 查找任务
@app.post("/search")
def search_task(request: Request, keyword: str = Form(...)):
    with get_db_conn() as conn:
        c = conn.cursor()
        # 使用 LIKE 搜索，注意 PostgreSQL 的占位符
        search_term = "%" + keyword + "%"
        c.execute("SELECT id, content FROM tasks WHERE content LIKE %s ORDER BY id", (search_term,))
        rows = c.fetchall()

    # 重新编号
    tasks = [{"seq": i + 1, "id": row[0], "content": row[1]} for i, row in enumerate(rows)]
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks, "search_keyword": keyword})