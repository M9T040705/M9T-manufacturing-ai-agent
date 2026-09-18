"""
运维管理模块 —— 投产必备
1. 版本管理和一键回退
2. 组件出错兜底
3. 数据备份和恢复
4. 系统日志和错误监控
"""
import shutil
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


class OpsManager:
    """运维管理：版本/备份/兜底/日志"""

    def __init__(self):
        self.version = "1.0.0"
        self.start_time = datetime.now()
        self.error_log: list[dict] = []  # 内存错误日志（最近100条）

    # ── 1. 版本管理和回退 ──────────────────
    def create_snapshot(self, name: str = "") -> dict:
        """
        创建配置快照（改配置前先拍个快照，出问题能回退）
        备份：vault规则、配置文件、上传数据
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = name or f"snapshot_{timestamp}"
        snapshot_dir = BACKUP_DIR / snapshot_name

        # 备份配置
        snapshot_dir.mkdir(exist_ok=True)

        # 备份vault规则
        vault_src = BASE_DIR / "vault"
        if vault_src.exists():
            shutil.copytree(vault_src, snapshot_dir / "vault", dirs_exist_ok=True)

        # 备份config
        config_src = BASE_DIR / "config"
        if config_src.exists():
            shutil.copytree(config_src, snapshot_dir / "config", dirs_exist_ok=True)

        # 备份上传数据
        data_src = BASE_DIR / "data" / "uploads"
        if data_src.exists():
            shutil.copytree(data_src, snapshot_dir / "uploads", dirs_exist_ok=True)

        # 备份数据库
        db_src = BASE_DIR / "data" / "app.db"
        if db_src.exists():
            shutil.copy(db_src, snapshot_dir / "app.db")

        return {
            "snapshot": snapshot_name,
            "path": str(snapshot_dir),
            "time": timestamp,
        }

    def rollback_snapshot(self, snapshot_name: str) -> dict:
        """
        一键回退到指定快照
        """
        snapshot_dir = BACKUP_DIR / snapshot_name
        if not snapshot_dir.exists():
            raise ValueError(f"快照不存在: {snapshot_name}")

        # 先拍当前状态
        self.create_snapshot(f"before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # 恢复vault
        vault_src = snapshot_dir / "vault"
        if vault_src.exists():
            vault_dst = BASE_DIR / "vault"
            if vault_dst.exists():
                shutil.rmtree(vault_dst)
            shutil.copytree(vault_src, vault_dst)

        # 恢复config
        config_src = snapshot_dir / "config"
        if config_src.exists():
            config_dst = BASE_DIR / "config"
            if config_dst.exists():
                shutil.rmtree(config_dst)
            shutil.copytree(config_src, config_dst)

        # 恢复数据库
        db_src = snapshot_dir / "app.db"
        if db_src.exists():
            db_dst = BASE_DIR / "data" / "app.db"
            shutil.copy(db_src, db_dst)

        return {"status": "rolled_back", "snapshot": snapshot_name}

    def list_snapshots(self) -> list[dict]:
        """列出所有快照"""
        snapshots = []
        if BACKUP_DIR.exists():
            for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
                if d.is_dir():
                    snapshots.append({
                        "name": d.name,
                        "time": d.name,
                    })
        return snapshots

    # ── 2. 组件出错兜底 ──────────────────
    def safe_call(self, func, fallback, *args, **kwargs):
        """
        安全调用：组件出错自动兜底
        单个组件挂了，整个系统还能跑
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_error(func.__name__ if hasattr(func, "__name__") else "unknown", str(e))
            return fallback

    def log_error(self, component: str, error: str):
        """记录错误日志"""
        entry = {
            "time": datetime.now().isoformat(),
            "component": component,
            "error": error,
            "traceback": traceback.format_exc()[:500],
        }
        self.error_log.append(entry)
        # 只保留最近100条
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]

        # 同时写文件日志
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{entry['time']}] {component}: {error}\n")

    # ── 3. 数据备份和恢复 ──────────────────
    def backup_database(self) -> dict:
        """备份数据库"""
        db_path = BASE_DIR / "data" / "app.db"
        if not db_path.exists():
            return {"status": "no_db"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"db_backup_{timestamp}.db"
        shutil.copy(db_path, backup_path)

        return {
            "status": "ok",
            "backup_file": str(backup_path),
            "size": backup_path.stat().st_size,
        }

    def restore_database(self, backup_file: str) -> dict:
        """从备份恢复数据库"""
        backup_path = BACKUP_DIR / backup_file
        if not backup_path.exists():
            raise ValueError(f"备份不存在: {backup_file}")

        db_path = BASE_DIR / "data" / "app.db"
        shutil.copy(backup_path, db_path)
        return {"status": "restored", "from": backup_file}

    # ── 4. 系统状态和日志 ──────────────────
    def get_system_status(self) -> dict:
        """系统整体状态"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        return {
            "version": self.version,
            "uptime": f"{hours}小时{minutes}分钟",
            "start_time": self.start_time.isoformat(),
            "recent_errors": len(self.error_log),
            "total_snapshots": len(list(BACKUP_DIR.iterdir())) if BACKUP_DIR.exists() else 0,
        }

    def get_error_logs(self, limit: int = 50) -> list[dict]:
        """获取最近错误日志"""
        return self.error_log[-limit:][::-1]  # 最新的在前
