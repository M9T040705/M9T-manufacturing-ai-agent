"""重置通知已读状态，让未读效果回来"""
import sqlite3
from pathlib import Path

db_path = Path(r"E:\fde\data\app.db")
conn = sqlite3.connect(str(db_path))
conn.execute("DELETE FROM notification_read")
conn.commit()
print(f"已清空已读记录，现在所有通知都是未读状态")
conn.close()
