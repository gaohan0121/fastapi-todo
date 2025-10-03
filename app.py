import os
# 需要安装：pip install psycopg2-binary python-dotenv
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# -----------------
# 1. 配置加载与连接
# -----------------

# 在本地开发时加载 .env 文件中的环境变量（如 DATABASE_URL）
# 在 Railway 部署时，它会自动忽略此行，并使用平台注入的环境变量
load_dotenv()

app = FastAPI()

# 静态文件 & 模板 (假设你有一个名为 'templates' 的文件夹)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 获取数据库连接URL (Railway/Render 会自动注入这个环境变量)
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_connection():
    """建立并返回一个 PostgreSQL 数据库连接"""
    if not DATABASE_URL:
        # 如果在本地运行但没有 .env 配置，会抛出错误
        raise ConnectionError("DATABASE_URL 环境变量未设置。请在 .env 文件中设置或在云平台配置。")

    # 连接到 Railway 提供的 PostgreSQL
    # 由于 Railway 的 DATABASE_URL 格式标准，可以直接连接
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# -----------------
# 2. 数据库初始化
# -----------------

def init_db():
    """启动时检查并创建 tasks 表"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # PostgreSQL 使用 SERIAL 作为自增主键
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"数据库初始化失败，请检查连接和 DATABASE_URL: {e}")
    finally:
        if conn:
            conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


# -----------------
# 3. 数据库操作（CRUD）
# -----------------

def get_tasks():
    """获取所有任务并添加序号"""
    conn = get_db_connection()
    c = conn.cursor()
    # 按 ID 排序
    c.execute("SELECT id, content FROM tasks ORDER BY id")
    rows = c.fetchall()
    conn.close()

    # 重新编号序号（seq 从 1 开始，用于前端展示）
    return [{"seq": i + 1, "id": row[0], "content": row[1]} for i, row in enumerate(rows)]


@app.get("/")
def read_root(request: Request):
    tasks = get_tasks()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})


@app.post("/add")
def add_task(content: str = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    # PostgreSQL 中参数占位符为 %s
    c.execute("INSERT INTO tasks (content) VALUES (%s)", (content,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{task_id}")
def delete_task(task_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/update/{task_id}")
def update_task(task_id: int, content: str = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET content = %s WHERE id = %s", (content, task_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/search")
def search_task(request: Request, keyword: str = Form(...)):
    conn = get_db_connection()
    c = conn.cursor()
    # 使用 PostgreSQL 的 LIKE 模糊查询
    c.execute("SELECT id, content FROM tasks WHERE content ILIKE %s", ('%' + keyword + '%',))
    rows = c.fetchall()
    conn.close()
    tasks = [{"seq": i + 1, "id": row[0], "content": row[1]} for i, row in enumerate(rows)]
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks, "search_keyword": keyword})