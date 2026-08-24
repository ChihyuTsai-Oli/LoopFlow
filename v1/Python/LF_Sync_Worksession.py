# -*- coding: utf-8 -*-
# Script: LF_Sync_Worksession.py (Worksession Real-Time Sync Monitor)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: After launch, monitors specified .3dm files in the background via FileSystemWatcher;
#           on detecting a change, auto-executes Worksession Refresh when Rhino is idle,
#           achieving real-time scene synchronisation between 3D and 2D files.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import System.IO
import scriptcontext as sc
import time
from typing import Optional
import _LoopFlow_Config as cfg

try:
    from _LF_Debug import log_exception
except Exception:
    log_exception = None

# ==================================================================
# Singleton Stop Guard
# ==================================================================
if 'ws_watcher' in sc.sticky:
    try:
        sc.sticky['ws_watcher'].stop()
        del sc.sticky['ws_watcher']
        print("Stopping existing LoopFlow Sync monitor...")
    except:
        pass

# ==================================================================
# WorksessionWatcher Class
# ==================================================================
class WorksessionWatcher:
    def __init__(self):
        self.doc_path = Rhino.RhinoDoc.ActiveDoc.Path
        if not self.doc_path:
            self.active = False
            return
            
        self.dir_path = System.IO.Path.GetDirectoryName(self.doc_path)
        self.active = True
        
        self.wait_seconds = cfg.SYNC_INTERVAL
        self.last_change_time = 0.0
        self.needs_refresh = False

        self.watcher = System.IO.FileSystemWatcher()
        self.watcher.Path = self.dir_path
        self.watcher.Filter = "*.3dm"
        self.watcher.NotifyFilter = System.IO.NotifyFilters.LastWrite
        self.watcher.Changed += self.on_event
        self.watcher.EnableRaisingEvents = True

        Rhino.RhinoApp.Idle += self.on_idle
        
        print(u"----- LoopFlow Sync Worksession Active -----")
        print(u"Watch directory: {}".format(self.dir_path))
        print(u"Detection delay: {} s".format(self.wait_seconds))

    def on_event(self, sender, e: System.IO.FileSystemEventArgs):
        try:
            if "~" in e.Name or "tmp" in e.Name.lower():
                return

            Rhino.RhinoApp.WriteLine(u"File change detected: {}".format(e.Name))
            self.last_change_time = time.time()
            self.needs_refresh = True
        except Exception as ex:
            if log_exception:
                Rhino.RhinoApp.WriteLine(log_exception("LF_Sync_Worksession.on_event", ex))

    def on_idle(self, sender, e):
        try:
            if self.needs_refresh:
                elapsed = time.time() - self.last_change_time
                if elapsed > self.wait_seconds:
                    self.needs_refresh = False
                    try:
                        success = Rhino.RhinoApp.RunScript("_-Worksession _Refresh _Enter", False)
                    except Exception as ex:
                        success = False
                        if log_exception:
                            Rhino.RhinoApp.WriteLine(log_exception("LF_Sync_Worksession.RunScript", ex))

                    if success:
                        Rhino.RhinoApp.WriteLine(u">>>>>>> LoopFlow Sync Worksession Updated (Delay: {}s)!".format(self.wait_seconds))
                    else:
                        Rhino.RhinoApp.WriteLine(">>>>>>> Notice: Rhino is busy; will retry at next idle point.")
                        self.needs_refresh = True
        except Exception as ex:
            if log_exception:
                Rhino.RhinoApp.WriteLine(log_exception("LF_Sync_Worksession.on_idle", ex))

    def stop(self):
        self.watcher.EnableRaisingEvents = False
        self.watcher.Changed -= self.on_event
        Rhino.RhinoApp.Idle -= self.on_idle
        self.active = False
        print("LoopFlow Sync Worksession stopped.")

# ==================================================================
# Entry Point
# ==================================================================
def main():
    try:
        watcher = WorksessionWatcher()
        if watcher.active:
            sc.sticky['ws_watcher'] = watcher
        else:
            import rhinoscriptsyntax as rs
            rs.MessageBox("Please save the file first before starting directory monitoring.", 48, "Startup Failed")
    except Exception as ex:
        if log_exception:
            Rhino.RhinoApp.WriteLine(log_exception("LF_Sync_Worksession.main", ex))

if __name__ == "__main__":
    main()