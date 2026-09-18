"""给state_store.py加通知已读功能"""
path = r"E:\fde\core\state_store.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 在末尾追加通知已读方法
addition = '''

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
'''

content += addition
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
