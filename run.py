"""Запуск тренажёра одной командой: `python run.py`.

Скрипт делает всё, что нужно для локального стенда:

1. создаёт виртуальное окружение `.venv`, если его нет;
2. ставит зависимости из `requirements.txt`;
3. наполняет базу демо-данными при первом запуске;
4. поднимает сервер и печатает адреса интерфейса и документации API.

Нужен только Python 3.11 или новее — ни Docker, ни Node, ни внешняя СУБД.
Флаги: `--port 8040`, `--no-seed` (не наполнять базу), `--reset` (пересоздать
базу с нуля).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
DB = ROOT / "data" / "trainer.db"
MIN_PYTHON = (3, 11)


def venv_python() -> Path:
    """Путь к интерпретатору внутри окружения — свой для Windows и Unix."""
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(args: list[str], **kwargs) -> None:
    subprocess.run(args, check=True, cwd=str(ROOT), **kwargs)


def ensure_venv() -> Path:
    """Создать окружение и поставить зависимости. Возвращает интерпретатор."""
    python = venv_python()
    if not python.exists():
        print("Создаю виртуальное окружение .venv …")
        run([sys.executable, "-m", "venv", str(VENV)])
    marker = VENV / ".requirements-installed"
    requirements = ROOT / "requirements.txt"
    if not marker.exists() or marker.stat().st_mtime < requirements.stat().st_mtime:
        print("Ставлю зависимости из requirements.txt …")
        run([str(python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", "--quiet", "-r", str(requirements)])
        marker.write_text("ok", encoding="utf-8")
    return python


def seed(python: Path, reset: bool) -> None:
    if reset and DB.exists():
        print("Пересоздаю базу …")
        DB.unlink()
    if DB.exists():
        return
    print("Наполняю базу демо-данными (5 проводников, рейтинг, токен интеграции) …")
    run([str(python), str(ROOT / "backend" / "seed.py")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Запуск тренажёра «Перегон»")
    parser.add_argument("--port", type=int, default=8040)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-seed", action="store_true", help="не наполнять базу демо-данными")
    parser.add_argument("--reset", action="store_true", help="пересоздать базу перед запуском")
    args = parser.parse_args()

    if sys.version_info < MIN_PYTHON:
        print(f"Нужен Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} или новее, а запущен {sys.version.split()[0]}")
        return 1

    python = ensure_venv()
    if not args.no_seed:
        seed(python, args.reset)

    print()
    print(f"  Интерфейс      http://{args.host}:{args.port}")
    print(f"  Документация   http://{args.host}:{args.port}/docs")
    print("  Остановить     Ctrl+C")
    print()
    try:
        run([
            str(python), "-m", "uvicorn", "app.main:app",
            "--app-dir", "backend",
            "--host", args.host,
            "--port", str(args.port),
        ])
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
