"""캡컷 자동 실행 + 프로젝트 로드 (Windows 전용)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import psutil

import config


def _find_capcut_executable() -> str | None:
    """캡컷 실행 파일 경로 탐색."""
    # 1. config에서 계산된 후보 경로 확인
    paths, _ = config.get_capcut_paths()
    for path in paths:
        if path and Path(path).exists():
            return path

    # 1-1. 사용자 프로필 하위 Apps 폴더 버전별 경로 탐색
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        apps_dir = Path(user_profile) / "AppData" / "Local" / "CapCut" / "Apps"
        if apps_dir.exists():
            # Apps/CapCut.exe
            root_exe = apps_dir / "CapCut.exe"
            if root_exe.exists():
                return str(root_exe)
            # Apps/<version>/CapCut.exe
            for exe in sorted(apps_dir.glob("*/CapCut.exe"), reverse=True):
                if exe.exists():
                    return str(exe)

    # 2. Windows 레지스트리 검색
    if os.name == "nt":
        try:
            import winreg
            # 2-a. 기존 CapCut 키
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hive, r"SOFTWARE\CapCut", 0, winreg.KEY_READ)
                    install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    winreg.CloseKey(key)
                    exe = Path(install_path) / "CapCut.exe"
                    if exe.exists():
                        return str(exe)
                except (FileNotFoundError, OSError):
                    pass

            # 2-b. Uninstall 레지스트리 (DisplayIcon/InstallLocation)
            uninstall_roots = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, root in uninstall_roots:
                try:
                    root_key = winreg.OpenKey(hive, root, 0, winreg.KEY_READ)
                except OSError:
                    continue

                idx = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(root_key, idx)
                    except OSError:
                        break
                    idx += 1
                    try:
                        sub_key = winreg.OpenKey(root_key, sub_name, 0, winreg.KEY_READ)
                    except OSError:
                        continue
                    try:
                        display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                    except OSError:
                        display_name = ""
                    if "capcut" not in str(display_name).lower():
                        winreg.CloseKey(sub_key)
                        continue

                    candidates: list[Path] = []
                    try:
                        icon, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
                        if icon:
                            candidates.append(Path(str(icon).split(",")[0].strip().strip('"')))
                    except OSError:
                        pass
                    try:
                        install_location, _ = winreg.QueryValueEx(sub_key, "InstallLocation")
                        if install_location:
                            candidates.append(Path(install_location) / "CapCut.exe")
                    except OSError:
                        pass

                    winreg.CloseKey(sub_key)
                    for c in candidates:
                        if c.exists():
                            return str(c)
                winreg.CloseKey(root_key)
        except ImportError:
            pass

    # 3. PATH 환경변수에서 검색
    capcut_in_path = shutil.which("CapCut") or shutil.which("capcut")
    if capcut_in_path:
        return capcut_in_path

    return None


def _is_capcut_running() -> bool:
    """캡컷 프로세스가 실행 중인지 확인."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and "capcut" in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def _wait_for_capcut(timeout: int = 30) -> bool:
    """캡컷이 로드될 때까지 대기."""
    start = time.time()
    while time.time() - start < timeout:
        if _is_capcut_running():
            return True
        time.sleep(1)
    return False


def launch_capcut(project_dir: Path) -> bool:
    """캡컷 자동 실행 + 프로젝트 로드.

    Args:
        project_dir: 캡컷 프로젝트 디렉토리 경로

    Returns:
        True: 성공, False: 실패 또는 미지원 환경
    """
    if os.name != "nt":
        print("  캡컷 자동 실행은 Windows에서만 지원됩니다.")
        print(f"  프로젝트 경로: {project_dir}")
        print("  Windows에서 캡컷을 열고 드래프트 목록에서 프로젝트를 선택하세요.")
        return False

    # 캡컷 실행 파일 찾기
    capcut_exe = _find_capcut_executable()
    if not capcut_exe:
        print("  캡컷이 설치되어 있지 않습니다.")
        print("  https://www.capcut.com 에서 캡컷 데스크톱 버전을 설치하세요.")
        print(f"  설치 후 {project_dir} 프로젝트를 수동으로 열어주세요.")
        return False

    # 이미 실행 중이면 건너뜀
    if _is_capcut_running():
        print("  캡컷이 이미 실행 중입니다.")
        print("  드래프트 목록에서 새 프로젝트를 확인하세요.")
        return True

    # 캡컷 실행
    try:
        subprocess.Popen([capcut_exe])
        print(f"  캡컷 실행 중... ({capcut_exe})")
    except OSError as e:
        print(f"  캡컷 실행 실패: {e}")
        return False

    # 로드 대기
    if _wait_for_capcut(timeout=30):
        print("  캡컷이 로드되었습니다!")
        print("  드래프트 목록에서 프로젝트를 확인하세요.")
        return True
    else:
        print("  캡컷 로드 대기 시간 초과 (30초)")
        print("  캡컷이 열리면 드래프트 목록에서 프로젝트를 확인하세요.")
        return False
