"""
状态层 —— 双模式：MySQL（生产）/ SQLite（演示/兜底）
对应Ha7ch经验：知识用文件，状态用事务。
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import pymysql

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "app.db"
DB_PATH.parent.mkdir(exist_ok=True)

# ── 数据库配置 ──────────────────────────
# 读 config/db.json，没有就用默认SQLite
CONFIG_PATH = BASE_DIR / "config" / "db.json"
CONFIG_PATH.parent.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "mode": "auto",  # auto / mysql / sqlite
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "fde_agent",
        "charset": "utf8mb4",
    },
}

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG

def _save_default_config():
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")

_save_default_config()
DB_CONFIG = _load_config()

# 角色 → 可访问的场景/页面映射
ROLE_PERMISSIONS = {
    "admin":      {"scenes": ["reconciliation","delivery","daily","kitting","equipment","quality"],
                   "pages": ["rules","upload","approval","audit"]},
    "manager":    {"scenes": ["reconciliation","delivery","daily","kitting","equipment","quality"],
                   "pages": ["approval"]},
    "finance":    {"scenes": ["reconciliation"], "pages": []},
    "sales":      {"scenes": ["delivery"], "pages": []},
    "production": {"scenes": ["kitting","daily","equipment"], "pages": []},
    "quality":    {"scenes": ["quality"], "pages": []},
}

ROLE_NAMES = {
    "admin": "系统管理员",
    "manager": "厂长/管理者",
    "finance": "财务",
    "sales": "销售",
    "production": "生产",
    "quality": "质量",
}


class StateStore:
    """对话历史 + 任务状态的持久层（MySQL / SQLite 双模式）"""

    def __init__(self):
        self._mode = self._detect_mode()
        self._init_db()

    def _detect_mode(self) -> str:
        """检测用哪种数据库"""
        mode = DB_CONFIG.get("mode", "auto")
        if mode == "sqlite":
            return "sqlite"
        if mode == "mysql":
            return "mysql"
        # auto：试连MySQL，连不上就用SQLite
        try:
            cfg = DB_CONFIG["mysql"]
            conn = pymysql.connect(
                host=cfg["host"], port=cfg["port"],
                user=cfg["user"], password=cfg["password"],
                database=cfg["database"], charset=cfg.get("charset", "utf8mb4"),
                connect_timeout=2,
            )
            conn.close()
            return "mysql"
        except Exception:
            return "sqlite"

    def _conn(self):
        if self._mode == "mysql":
            cfg = DB_CONFIG["mysql"]
            return pymysql.connect(
                host=cfg["host"], port=cfg["port"],
                user=cfg["user"], password=cfg["password"],
                database=cfg["database"], charset=cfg.get("charset", "utf8mb4"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        else:
            return sqlite3.connect(str(DB_PATH))

    def _q(self, sql: str):
        """占位符转换：MySQL用%s，SQLite用?"""
        if self._mode == "mysql":
            return sql.replace("?", "%s")
        return sql

    def _row(self, row):
        """统一行格式：MySQL返回dict，SQLite返回tuple，转成统一dict"""
        if self._mode == "mysql":
            return row
        return row  # SQLite走索引访问，保持原样

    def _init_db(self):
        if self._mode == "mysql":
            self._init_mysql()
        else:
            self._init_sqlite()
        self._create_default_users()

    def _init_sqlite(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    scene TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    finished_at TEXT
                );
                CREATE TABLE IF NOT EXISTS problem_model (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    bottleneck TEXT, causal_chain TEXT, impact TEXT,
                    stakeholders TEXT, previous_attempt TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    comment TEXT,
                    user TEXT,
                    created_at TEXT NOT NULL
                );
            """)

    def _init_mysql(self):
        with self._conn() as c:
            cur = c.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scene VARCHAR(50) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    intent VARCHAR(100),
                    created_at VARCHAR(50) NOT NULL,
                    INDEX idx_scene (scene)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(100) PRIMARY KEY,
                    scene VARCHAR(50),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    summary TEXT,
                    created_at VARCHAR(50) NOT NULL,
                    finished_at VARCHAR(50)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS problem_model (
                    id INT PRIMARY KEY,
                    bottleneck TEXT, causal_chain TEXT, impact TEXT,
                    stakeholders TEXT, previous_attempt TEXT, updated_at VARCHAR(50)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(100) NOT NULL,
                    display_name VARCHAR(50) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    department VARCHAR(50),
                    created_at VARCHAR(50) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scene VARCHAR(50) NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    rating VARCHAR(20) NOT NULL,
                    comment TEXT,
                    user VARCHAR(50),
                    created_at VARCHAR(50) NOT NULL,
                    INDEX idx_scene (scene),
                    INDEX idx_rating (rating)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

    def _create_default_users(self):
        default_users = [
            ("admin", "admin123", "系统管理员", "admin", "IT部"),
            ("boss", "boss123", "厂长", "manager", "厂部"),
            ("finance", "fin123", "财务王姐", "finance", "财务部"),
            ("sales", "sales123", "销售小李", "sales", "销售部"),
            ("prod", "prod123", "生产张工", "production", "生产部"),
            ("qc", "qc123", "质量陈工", "quality", "质量部"),
        ]
        with self._conn() as c:
            cur = c.cursor()
            for username, pwd, name, role, dept in default_users:
                if self._mode == "mysql":
                    cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                else:
                    cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
                exists = cur.fetchone()
                if not exists:
                    if self._mode == "mysql":
                        cur.execute(
                            "INSERT INTO users (username, password_hash, display_name, role, department, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
                            (username, self._hash(pwd), name, role, dept, datetime.now().isoformat()),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO users (username, password_hash, display_name, role, department, created_at) VALUES (?,?,?,?,?,?)",
                            (username, self._hash(pwd), name, role, dept, datetime.now().isoformat()),
                        )

    @staticmethod
    def _hash(pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

    def verify_user(self, username: str, password: str) -> Optional[dict]:
        pwd_hash = self._hash(password)
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "SELECT id, username, display_name, role, department FROM users WHERE username=%s AND password_hash=%s",
                    (username, pwd_hash),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {"id": row["id"], "username": row["username"], "display_name": row["display_name"],
                        "role": row["role"], "department": row["department"]}
            else:
                row = cur.execute(
                    "SELECT id, username, display_name, role, department FROM users WHERE username=? AND password_hash=?",
                    (username, pwd_hash),
                ).fetchone()
                if not row:
                    return None
                return {"id": row[0], "username": row[1], "display_name": row[2], "role": row[3], "department": row[4]}

    def user_permissions(self, role: str) -> dict:
        return ROLE_PERMISSIONS.get(role, {"scenes": [], "pages": []})

    # ── 对话历史 ──────────────────────────
    def save_message(self, scene: str, role: str, content: str, intent: str = ""):
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "INSERT INTO chat_history (scene, role, content, intent, created_at) VALUES (%s,%s,%s,%s,%s)",
                    (scene, role, content, intent, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT INTO chat_history (scene, role, content, intent, created_at) VALUES (?,?,?,?,?)",
                    (scene, role, content, intent, datetime.now().isoformat()),
                )

    def get_history(self, scene: str, limit: int = 50) -> list[dict]:
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "SELECT role, content, intent, created_at FROM chat_history WHERE scene=%s ORDER BY id DESC LIMIT %s",
                    (scene, limit),
                )
                rows = cur.fetchall()
                return [{"role": r["role"], "content": r["content"], "intent": r["intent"], "time": r["created_at"]} for r in reversed(rows)]
            else:
                rows = cur.execute(
                    "SELECT role, content, intent, created_at FROM chat_history WHERE scene=? ORDER BY id DESC LIMIT ?",
                    (scene, limit),
                ).fetchall()
                return [{"role": r[0], "content": r[1], "intent": r[2], "time": r[3]} for r in reversed(rows)]

    def clear_history(self, scene: str = None):
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                if scene:
                    cur.execute("DELETE FROM chat_history WHERE scene=%s", (scene,))
                else:
                    cur.execute("DELETE FROM chat_history")
            else:
                if scene:
                    cur.execute("DELETE FROM chat_history WHERE scene=?", (scene,))
                else:
                    cur.execute("DELETE FROM chat_history")

    # ── 问题模型 ──────────────────────────
    def save_problem_model(self, bottleneck, causal_chain, impact, stakeholders, previous_attempt):
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("""
                    INSERT INTO problem_model
                    (id, bottleneck, causal_chain, impact, stakeholders, previous_attempt, updated_at)
                    VALUES (1,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                    bottleneck=VALUES(bottleneck), causal_chain=VALUES(causal_chain),
                    impact=VALUES(impact), stakeholders=VALUES(stakeholders),
                    previous_attempt=VALUES(previous_attempt), updated_at=VALUES(updated_at)
                """, (bottleneck, causal_chain, impact, stakeholders, previous_attempt, datetime.now().isoformat()))
            else:
                cur.execute("""
                    INSERT OR REPLACE INTO problem_model
                    (id, bottleneck, causal_chain, impact, stakeholders, previous_attempt, updated_at)
                    VALUES (1,?,?,?,?,?,?)
                """, (bottleneck, causal_chain, impact, stakeholders, previous_attempt, datetime.now().isoformat()))

    def get_problem_model(self) -> Optional[dict]:
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("SELECT * FROM problem_model WHERE id=1")
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "bottleneck": row["bottleneck"], "causal_chain": row["causal_chain"],
                    "impact": row["impact"], "stakeholders": row["stakeholders"],
                    "previous_attempt": row["previous_attempt"], "updated_at": row["updated_at"],
                }
            else:
                row = cur.execute("SELECT * FROM problem_model WHERE id=1").fetchone()
                if not row:
                    return None
                return {
                    "bottleneck": row[1], "causal_chain": row[2], "impact": row[3],
                    "stakeholders": row[4], "previous_attempt": row[5], "updated_at": row[6],
                }

    # ── 用户反馈（自进化：越用越准）─────────
    def save_feedback(self, scene, question, answer, rating, comment, user):
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "INSERT INTO feedback (scene, question, answer, rating, comment, user, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (scene, question, answer, rating, comment, user, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT INTO feedback (scene, question, answer, rating, comment, user, created_at) VALUES (?,?,?,?,?,?,?)",
                    (scene, question, answer, rating, comment, user, datetime.now().isoformat()),
                )

    def get_good_examples(self, scene: str, limit: int = 5) -> list[dict]:
        """获取该场景的用户认可案例（👍）"""
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "SELECT question, answer FROM feedback WHERE scene=%s AND rating='good' ORDER BY id DESC LIMIT %s",
                    (scene, limit),
                )
                return [{"question": r["question"], "answer": r["answer"]} for r in cur.fetchall()]
            else:
                rows = cur.execute(
                    "SELECT question, answer FROM feedback WHERE scene=? AND rating='good' ORDER BY id DESC LIMIT ?",
                    (scene, limit),
                ).fetchall()
                return [{"question": r[0], "answer": r[1]} for r in rows]

    def get_feedback_stats(self) -> dict:
        """反馈统计"""
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("SELECT COUNT(*) as cnt FROM feedback")
                total = cur.fetchone()["cnt"]
                cur.execute("SELECT COUNT(*) as cnt FROM feedback WHERE rating='good'")
                good = cur.fetchone()["cnt"]
                cur.execute("SELECT COUNT(*) as cnt FROM feedback WHERE rating='bad'")
                bad = cur.fetchone()["cnt"]
            else:
                total = cur.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
                good = cur.execute("SELECT COUNT(*) FROM feedback WHERE rating='good'").fetchone()[0]
                bad = cur.execute("SELECT COUNT(*) FROM feedback WHERE rating='bad'").fetchone()[0]
        return {"total": total, "good": good, "bad": bad}

    @property
    def mode(self):
        """当前使用的数据库模式"""
        return self._mode

    # ── 用户管理（管理员用）─────────────────
    def list_users(self) -> list[dict]:
        """列出所有用户"""
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("SELECT id, username, display_name, role, department, created_at FROM users ORDER BY id")
                return [{"id": r["id"], "username": r["username"], "display_name": r["display_name"],
                         "role": r["role"], "role_name": ROLE_NAMES.get(r["role"], r["role"]),
                         "department": r["department"], "created_at": r["created_at"]} for r in cur.fetchall()]
            else:
                rows = cur.execute("SELECT id, username, display_name, role, department, created_at FROM users ORDER BY id").fetchall()
                return [{"id": r[0], "username": r[1], "display_name": r[2],
                         "role": r[3], "role_name": ROLE_NAMES.get(r[3], r[3]),
                         "department": r[4], "created_at": r[5]} for r in rows]

    def create_user(self, username: str, password: str, display_name: str, role: str, department: str = "") -> dict:
        """创建新用户"""
        if role not in ROLE_PERMISSIONS:
            raise ValueError(f"无效角色: {role}")
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
            else:
                cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
            if cur.fetchone():
                raise ValueError(f"用户名 {username} 已存在")
            if self._mode == "mysql":
                cur.execute(
                    "INSERT INTO users (username, password_hash, display_name, role, department, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (username, self._hash(password), display_name, role, department, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT INTO users (username, password_hash, display_name, role, department, created_at) VALUES (?,?,?,?,?,?)",
                    (username, self._hash(password), display_name, role, department, datetime.now().isoformat()),
                )
        return {"username": username, "display_name": display_name, "role": role}

    def delete_user(self, user_id: int):
        """删除用户"""
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            else:
                cur.execute("DELETE FROM users WHERE id=?", (user_id,))

    def reset_password(self, user_id: int, new_password: str):
        """重置密码"""
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (self._hash(new_password), user_id))
            else:
                cur.execute("UPDATE users SET password_hash=? WHERE id=?", (self._hash(new_password), user_id))

    def list_roles(self) -> list[dict]:
        """列出所有可选角色"""
        return [{"key": k, "name": v} for k, v in ROLE_NAMES.items()]


    # ── 通知已读状态 ──────────────────────────
    def _ensure_notif_table(self):
        """确保通知已读表存在"""
        if self._mode == "mysql":
            with self._conn() as c:
                cur = c.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notification_read (
                        notif_id VARCHAR(100) PRIMARY KEY,
                        user VARCHAR(50),
                        read_at VARCHAR(50)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
        else:
            with self._conn() as c:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS notification_read (
                        notif_id TEXT PRIMARY KEY,
                        user TEXT,
                        read_at TEXT
                    )
                """)

    def mark_notif_read(self, notif_id: str, user: str):
        """标记通知为已读"""
        self._ensure_notif_table()
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute(
                    "INSERT IGNORE INTO notification_read (notif_id, user, read_at) VALUES (%s,%s,%s)",
                    (notif_id, user, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT OR IGNORE INTO notification_read (notif_id, user, read_at) VALUES (?,?,?)",
                    (notif_id, user, datetime.now().isoformat()),
                )

    def mark_all_read(self, user: str):
        """标记该用户所有通知为已读（通过传所有当前未读id）"""
        self._ensure_notif_table()
        # 这个方法在API层处理，这里留空
        pass

    def get_read_notifs(self, user: str) -> set:
        """获取该用户已读的通知ID集合"""
        self._ensure_notif_table()
        with self._conn() as c:
            cur = c.cursor()
            if self._mode == "mysql":
                cur.execute("SELECT notif_id FROM notification_read WHERE user=%s", (user,))
                return {r["notif_id"] for r in cur.fetchall()}
            else:
                rows = cur.execute("SELECT notif_id FROM notification_read WHERE user=?", (user,)).fetchall()
                return {r[0] for r in rows}
