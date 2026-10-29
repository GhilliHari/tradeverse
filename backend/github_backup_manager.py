"""
GitHub Backup & Cloud Support Manager for Tradeverse
====================================================
Ensures all Tradeverse backup data is stored in GitHub (`GhilliHari/tradeverse`)
and supported/restored directly from GitHub across local, daemon, and cloud environments:
  - Simulation Observatory journals (`backend/observatory_data/simulation_*.json`)
  - Latest Observatory & Paper Trade snapshot (`backend/observatory_data/latest_summary.json`)
  - Paper Trading ledger (`backend/data/paper_trades.jsonl`)
  - Historical & 5m Intraday Market Cache (`backend/data/cache/*.csv`)
  - Knowledge Base & AI Model Configs (`backend/knowledge_base/`, `backend/*.joblib`, `backend/*.pth`)
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.request

logger = logging.getLogger("GITHUB_BACKUP")

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OBSERVATORY_DIR = BACKEND_DIR / "observatory_data"
KNOWLEDGE_DIR = BACKEND_DIR / "knowledge_base"

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "GhilliHari/tradeverse")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
RAW_GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"


class GitHubBackupManager:
    """Manages bidirectional backup storage and fallback support from GitHub."""

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.backend_dir = BACKEND_DIR
        self.data_dir = DATA_DIR
        self.cache_dir = CACHE_DIR
        self.observatory_dir = OBSERVATORY_DIR
        self.manifest_path = self.data_dir / "backup_manifest.json"
        self.latest_summary_path = self.observatory_dir / "latest_summary.json"
        self.last_sync_status: Dict[str, Any] = {}

    def _run_git(self, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Executes a git command inside the repository root without interactive password prompts."""
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        return subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )

    def generate_backup_manifests(
        self,
        sim_status: Optional[Dict[str, Any]] = None,
        sim_summary: Optional[Dict[str, Any]] = None,
        sim_results: Optional[Dict[str, Any]] = None,
        paper_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates `backend/observatory_data/latest_summary.json` and
        `backend/data/backup_manifest.json` so both backend and frontend can
        load complete state directly from GitHub Raw URLs even when offline.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.observatory_dir.mkdir(parents=True, exist_ok=True)

        # Lazily query simulation_engine and paper_manager if not passed in
        try:
            if sim_status is None or sim_summary is None or sim_results is None:
                from simulation_engine import simulation_engine
                sim_status = sim_status or simulation_engine.get_status()
                sim_summary = sim_summary or simulation_engine.get_accuracy_summary()
                sim_results = sim_results or simulation_engine.get_results()
        except Exception as e:
            logger.warning(f"Could not query simulation_engine for manifest: {e}")
            sim_status = sim_status or {}
            sim_summary = sim_summary or {}
            sim_results = sim_results or {"predictions": []}

        try:
            if paper_summary is None:
                from paper_manager import paper_manager
                paper_summary = paper_manager.get_summary()
        except Exception as e:
            logger.warning(f"Could not query paper_manager for manifest: {e}")
            paper_summary = paper_summary or {}

        predictions = sim_results.get("predictions", []) if isinstance(sim_results, dict) else []
        sorted_preds = sorted(
            predictions,
            key=lambda p: p.get("timestamp", ""),
            reverse=True
        )[:30]

        now_iso = datetime.now().isoformat()

        latest_payload = {
            "updated_at": now_iso,
            "repo": GITHUB_REPO,
            "branch": GITHUB_BRANCH,
            "status": sim_status,
            "observatory_summary": sim_summary,
            "recent_predictions": sorted_preds,
            "paper_summary": paper_summary,
        }

        with open(self.latest_summary_path, "w") as f:
            json.dump(latest_payload, f, indent=2)

        obs_files = sorted(
            [p.name for p in self.observatory_dir.glob("simulation_*.json")]
        )
        cache_files = sorted(
            [p.name for p in self.cache_dir.glob("*.csv")]
        ) if self.cache_dir.exists() else []

        paper_trades_file = self.data_dir / "paper_trades.jsonl"
        paper_lines_count = 0
        if paper_trades_file.exists():
            with open(paper_trades_file, "r") as f:
                paper_lines_count = sum(1 for line in f if line.strip())

        manifest = {
            "updated_at": now_iso,
            "repo": GITHUB_REPO,
            "branch": GITHUB_BRANCH,
            "raw_base_url": RAW_GITHUB_BASE,
            "latest_session_date": sim_summary.get("date") or paper_summary.get("date"),
            "observatory_files_count": len(obs_files),
            "observatory_files": obs_files,
            "market_cache_files_count": len(cache_files),
            "market_cache_files": cache_files,
            "paper_trades_entries": paper_lines_count,
            "all_time_closed_trades": paper_summary.get("all_time_closed", 0),
            "all_time_pnl": paper_summary.get("all_time_pnl", 0.0),
        }

        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def get_backup_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of local & GitHub-backed data files."""
        manifest = {}
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r") as f:
                    manifest = json.load(f)
            except Exception:
                manifest = {}
        else:
            manifest = self.generate_backup_manifests()

        commit_hash = "unknown"
        commit_time = None
        remote_url = f"https://github.com/{GITHUB_REPO}"
        pending_changes = 0

        try:
            rev = self._run_git(["rev-parse", "--short", "HEAD"], timeout=10)
            if rev.returncode == 0:
                commit_hash = rev.stdout.strip()

            ct = self._run_git(["log", "-1", "--format=%cI"], timeout=10)
            if ct.returncode == 0:
                commit_time = ct.stdout.strip()

            st = self._run_git(
                ["status", "--porcelain", "backend/data", "backend/observatory_data", "backend/knowledge_base"],
                timeout=10
            )
            if st.returncode == 0:
                pending_changes = len([ln for ln in st.stdout.splitlines() if ln.strip()])
        except Exception as e:
            logger.debug(f"Git status check failed: {e}")

        return {
            "status": "ONLINE",
            "provider": "GitHub",
            "repo": GITHUB_REPO,
            "branch": GITHUB_BRANCH,
            "repo_url": remote_url,
            "raw_base_url": RAW_GITHUB_BASE,
            "latest_commit": commit_hash,
            "last_commit_time": commit_time,
            "pending_backup_changes": pending_changes,
            "is_synced": pending_changes == 0,
            "observatory_files_count": manifest.get("observatory_files_count", 0),
            "market_cache_files_count": manifest.get("market_cache_files_count", 0),
            "paper_trades_entries": manifest.get("paper_trades_entries", 0),
            "latest_session_date": manifest.get("latest_session_date"),
            "last_sync_result": self.last_sync_status,
        }

    def backup_to_github(self, commit_message: Optional[str] = None, push: bool = True) -> Dict[str, Any]:
        """
        Stages all backup data (`backend/data`, `backend/observatory_data`,
        `backend/knowledge_base`, model configs), commits, and pushes to GitHub.
        """
        manifest = self.generate_backup_manifests()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        msg = commit_message or f"chore(backup): sync simulation, paper trades & market cache [{now_str}]"

        paths_to_stage = [
            "backend/data",
            "backend/observatory_data",
            "backend/knowledge_base",
            ".gitignore",
        ]

        try:
            for rel_path in paths_to_stage:
                full = self.repo_root / rel_path
                if full.exists():
                    self._run_git(["add", "-f", rel_path], timeout=30)

            diff_check = self._run_git(["diff", "--cached", "--quiet"], timeout=15)
            committed = False
            if diff_check.returncode != 0:
                commit_proc = self._run_git(["commit", "-m", msg], timeout=30)
                committed = commit_proc.returncode == 0
                if not committed:
                    logger.warning(f"Git commit warning: {commit_proc.stderr}")

            pushed = False
            push_error = None
            if push:
                push_proc = self._run_git(["push", "origin", GITHUB_BRANCH], timeout=90)
                pushed = push_proc.returncode == 0
                if not pushed:
                    push_error = push_proc.stderr.strip()
                    logger.warning(f"Git push warning: {push_error}")

            rev = self._run_git(["rev-parse", "--short", "HEAD"], timeout=10)
            commit_hash = rev.stdout.strip() if rev.returncode == 0 else "unknown"

            result = {
                "status": "success" if (pushed or not push) else "committed_locally",
                "committed": committed,
                "pushed": pushed,
                "commit_hash": commit_hash,
                "timestamp": datetime.now().isoformat(),
                "repo": GITHUB_REPO,
                "branch": GITHUB_BRANCH,
                "observatory_files_count": manifest.get("observatory_files_count", 0),
                "market_cache_files_count": manifest.get("market_cache_files_count", 0),
                "paper_trades_entries": manifest.get("paper_trades_entries", 0),
                "push_error": push_error,
            }
            self.last_sync_status = result
            return result
        except Exception as e:
            logger.error(f"GitHub backup failed: {e}")
            err_res = {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.last_sync_status = err_res
            return err_res

    def _download_raw_file(self, rel_repo_path: str, dest_path: Path) -> bool:
        """Downloads a single file directly from GitHub Raw URL as fallback."""
        url = f"{RAW_GITHUB_BASE}/{rel_repo_path.lstrip('/')}"
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Tradeverse-Backup-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    logger.info(f"📥 Restored {rel_repo_path} from GitHub Raw ({len(data)} bytes)")
                    return True
        except Exception as e:
            logger.debug(f"Could not fetch {url}: {e}")
        return False

    def restore_from_github(self, force_checkout: bool = False) -> Dict[str, Any]:
        """
        Restores/supports backup data from GitHub (`origin/main` or Raw GitHub API).
        Ensures `backend/data/paper_trades.jsonl`, `backend/observatory_data/simulation_*.json`,
        and `backend/data/cache/*.csv` are present locally.
        """
        restored_files: List[str] = []
        git_fetched = False

        # 1. Try git fetch + checkout of missing or requested backup files
        try:
            fetch_proc = self._run_git(["fetch", "origin", GITHUB_BRANCH], timeout=45)
            git_fetched = fetch_proc.returncode == 0
            if git_fetched and force_checkout:
                co_proc = self._run_git(
                    ["checkout", f"origin/{GITHUB_BRANCH}", "--", "backend/data", "backend/observatory_data"],
                    timeout=30
                )
                if co_proc.returncode == 0:
                    restored_files.append("backend/data/* & backend/observatory_data/* (git checkout)")
        except Exception as e:
            logger.debug(f"Git fetch during restore failed: {e}")

        # 2. Check individual critical files and restore from git or GitHub Raw if missing
        critical_rel_paths = [
            "backend/data/backup_manifest.json",
            "backend/data/paper_trades.jsonl",
            "backend/observatory_data/latest_summary.json",
        ]
        for rel_path in critical_rel_paths:
            local_file = self.repo_root / rel_path
            if not local_file.exists() or local_file.stat().st_size == 0:
                co = self._run_git(["checkout", f"origin/{GITHUB_BRANCH}", "--", rel_path], timeout=15)
                if co.returncode == 0 and local_file.exists():
                    restored_files.append(rel_path)
                elif self._download_raw_file(rel_path, local_file):
                    restored_files.append(rel_path)

        # 3. If manifest exists, ensure all listed observatory & cache files exist locally
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r") as f:
                    manifest = json.load(f)
                for obs_name in manifest.get("observatory_files", []):
                    obs_local = self.observatory_dir / obs_name
                    rel = f"backend/observatory_data/{obs_name}"
                    if not obs_local.exists():
                        co = self._run_git(["checkout", f"origin/{GITHUB_BRANCH}", "--", rel], timeout=15)
                        if co.returncode == 0 and obs_local.exists():
                            restored_files.append(rel)
                        elif self._download_raw_file(rel, obs_local):
                            restored_files.append(rel)

                for csv_name in manifest.get("market_cache_files", []):
                    csv_local = self.cache_dir / csv_name
                    rel = f"backend/data/cache/{csv_name}"
                    if not csv_local.exists():
                        co = self._run_git(["checkout", f"origin/{GITHUB_BRANCH}", "--", rel], timeout=15)
                        if co.returncode == 0 and csv_local.exists():
                            restored_files.append(rel)
                        elif self._download_raw_file(rel, csv_local):
                            restored_files.append(rel)
            except Exception as e:
                logger.warning(f"Manifest restore check warning: {e}")

        return {
            "status": "success",
            "repo": GITHUB_REPO,
            "branch": GITHUB_BRANCH,
            "git_fetched": git_fetched,
            "restored_files_count": len(restored_files),
            "restored_files": restored_files,
            "timestamp": datetime.now().isoformat(),
        }


github_backup_manager = GitHubBackupManager()
