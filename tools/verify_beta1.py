#!/usr/bin/env python3
"""Selected Beta 1 checks; each test gets isolated GUI settings and subprocess state."""
import argparse
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    'test_beta1_startup_v1.py',
    'test_beta1b_project_folders_v1.py',
    'test_beta1c_twenty_room_sample_v1.py',
    'test_beta1d_sample_opening_view_v1.py',
    'test_beta1_entrypoint_v1.py',
    'test_hls2c3a_single_project_folder_save_as_v1.py',
    'test_hls2c3b_compact_live_project_panel_v1.py',
    'test_hls2b2_wall_wizard_mutation_dirty_refresh_v1.py',
    'test_hls2b2a_wall_wizard_project_room_lifecycle_v1.py',
    'test_hs69b3k1_animated_startup_splash_v1.py',
    'test_hs72a4f_navigation_integration_v1.py',
    'test_hs74a_topology_guidance_v1.py',
    'test_hs74a_topology_help_integration_v1.py',
    'test_hs73a_pump_duty_preview_v1.py',
    'test_hs73b_pump_duty_v1.py',
    'test_hs73b_pump_duty_gui_v1.py',
    'test_hs73b1_pump_route_identity_v1.py',
    'test_hs73b2_pump_density_defaults_v1.py',
    'test_hs73c_shared_water_properties_v1.py',
    'test_hs73c_shared_water_gui_v1.py',
    'test_hs73c2_kvs_editor_drafts_v1.py',
)


def worker(test, temporary):
    import runpy
    from unittest.mock import patch
    from PySide6.QtCore import QSettings
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    QSettings.setPath(QSettings.NativeFormat, QSettings.UserScope, str(temporary/'qt'))
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(temporary/'qt'))
    # Settings code asks Path.home(); do not alter the user's real settings.
    with patch.object(Path, 'home', return_value=temporary), patch(
        'HVAC.gui_v3.context.project_workspace_v1.default_project_root_v1',
        return_value=temporary/'HVACprojects',
    ):
        sys.argv = [str(ROOT/'HVAC/dev'/test)]
        runpy.run_path(sys.argv[0], run_name='__main__')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', choices=TESTS)
    parser.add_argument('--temporary', type=Path)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker,args.temporary);return
    failures=[]
    for test in TESTS:
        with tempfile.TemporaryDirectory(prefix='hvacgooee-beta1-') as temporary:
            env={**os.environ,'QT_QPA_PLATFORM':'offscreen','PYTHONPATH':str(ROOT),
                 'XDG_CONFIG_HOME':temporary+'/config','XDG_DATA_HOME':temporary+'/data'}
            try:
                result=subprocess.run([sys.executable,str(Path(__file__).resolve()),
                    '--worker',test,'--temporary',temporary],cwd=ROOT,env=env,
                    text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
                passed=result.returncode==0
                print(('PASS ' if passed else 'FAIL ')+test,flush=True)
                if not passed:print(result.stdout)
            except subprocess.TimeoutExpired:
                passed=False;print('TIMEOUT '+test,flush=True)
            if not passed:failures.append(test)
    print(f'{len(TESTS)-len(failures)}/{len(TESTS)} selected Beta 1 checks passed.')
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
