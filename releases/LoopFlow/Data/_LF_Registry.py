# -*- coding: utf-8 -*-
# Script: _LF_Registry.py (Project_Registry.json Read/Write Bridge)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Debug.py
# Usage: Provides the RegistryCenter class encapsulating Project_Registry.json read/write,
#           with collision-prevention lock (.lock) and atomic write mechanism.
#           Referenced by LF_Push_3D_to_JSON, LF_Infuser_Part/All, LF_Tagger_Layout_ID.
#           Not intended for direct execution.

# ==================================================================
# Imports
# ==================================================================
import json
import os
import time
import io

try:
    from _LoopFlow_Config import REGISTRY_FILENAME, REGISTRY_LOCK_FILENAME, LOCK_TIMEOUT, STALE_LOCK_SECONDS
except Exception:
    REGISTRY_FILENAME      = "Project_Registry.json"
    REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
    LOCK_TIMEOUT           = 8.0
    STALE_LOCK_SECONDS     = 120.0

try:
    from _LF_Debug import log_exception
except Exception:
    log_exception = None

# ==================================================================
# RegistryCenter Class
# ==================================================================
class RegistryCenter:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.json_path = os.path.join(project_dir, REGISTRY_FILENAME)
        self.lock_path = os.path.join(project_dir, REGISTRY_LOCK_FILENAME)
        self._ensure_registry_exists()

    def _ensure_registry_exists(self):
        if not os.path.exists(self.json_path):
            initial_data = {
                "Global_Status": {
                    "Last_Sync_Time": time.time(),
                    "Version": "1.0.0"
                },
                "Objects": {},
                "Layout_Map": {},
                "Tag_Links": {}
            }
            self._write_json(initial_data)

# ==================================================================
#   File Locking
# ==================================================================
    def _read_lock_timestamp(self):
        """Parse ts=<float> inside the .lock file. Falls back to os.path.getmtime()
        when the content is unreadable. Preferring the in-file timestamp avoids
        false-fresh detection on Dropbox/OneDrive folders where cloud sync
        repeatedly touches mtime."""
        try:
            with io.open(self.lock_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ts="):
                        try:
                            return float(line.split("=", 1)[1])
                        except Exception:
                            break
        except Exception:
            pass
        try:
            return os.path.getmtime(self.lock_path)
        except OSError:
            return None

    def _acquire_lock(self, timeout=LOCK_TIMEOUT, stale_seconds=STALE_LOCK_SECONDS):
        start_time = time.time()
        while os.path.exists(self.lock_path):
            lock_ts = self._read_lock_timestamp()
            if stale_seconds and lock_ts is not None:
                if (time.time() - lock_ts) > stale_seconds:
                    try:
                        os.remove(self.lock_path)
                        continue
                    except OSError:
                        pass

            if time.time() - start_time > timeout:
                print(u"Warning: Registry is currently locked by another process; write timed out.\n  Lock file: {}".format(self.lock_path))
                return False
            time.sleep(0.3)

        try:
            with io.open(self.lock_path, 'w', encoding='utf-8') as f:
                f.write(u"ts={}\n".format(time.time()))
            return True
        except IOError as e:
            if log_exception:
                print(log_exception(u"_LF_Registry._acquire_lock", e))
            return False

    def _release_lock(self):
        if os.path.exists(self.lock_path):
            try:
                os.remove(self.lock_path)
            except OSError:
                pass

    def force_unlock(self):
        """Public API: forcibly remove a stale .lock file. Useful after a crashed
        Rhino session or when a cloud-sync folder left a leftover lock behind.
        Returns True if the lock is gone (either removed or never existed)."""
        if not os.path.exists(self.lock_path):
            return True
        for _ in range(3):
            try:
                os.remove(self.lock_path)
                return True
            except OSError:
                time.sleep(0.3)
        return not os.path.exists(self.lock_path)

# ==================================================================
#   JSON I/O
# ==================================================================
    def _read_json(self):
        if not os.path.exists(self.json_path):
            return {}
        try:
            with io.open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            if log_exception:
                print(log_exception(u"_LF_Registry._read_json.JSONDecodeError", e))
            print("Error: JSON format corrupted; cannot parse.")
            return {}
        except Exception as e:
            if log_exception:
                print(log_exception(u"_LF_Registry._read_json", e))
            return {}

    def _write_json(self, data):
        if self._acquire_lock():
            try:
                data["Global_Status"]["Last_Sync_Time"] = time.time()
                tmp_path = self.json_path + ".tmp"
                with io.open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass
                # Retry os.replace a few times: cloud-sync clients (Dropbox /
                # OneDrive) occasionally hold the target file briefly.
                last_err = None
                for i in range(5):
                    try:
                        os.replace(tmp_path, self.json_path)
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        time.sleep(0.3 * (i + 1))
                if last_err is not None:
                    try:
                        if os.path.exists(self.json_path):
                            os.remove(self.json_path)
                        os.rename(tmp_path, self.json_path)
                    except Exception:
                        raise last_err
            finally:
                self._release_lock()
            return True
        return False

# ==================================================================
#   Public API
# ==================================================================
    def push_3d_objects(self, objects_dict):
        data = self._read_json()
        if not data: return False

        data["Objects"] = objects_dict
        return self._write_json(data)

    def push_layout_map(self, layout_dict):
        data = self._read_json()
        if not data: return False
        
        data["Layout_Map"] = layout_dict
        return self._write_json(data)

    def push_tag_links(self, tag_links_dict):
        data = self._read_json()
        if not data: return False
        
        data.setdefault("Tag_Links", {}).update(tag_links_dict)
        return self._write_json(data)

    def get_full_registry(self):
        return self._read_json()