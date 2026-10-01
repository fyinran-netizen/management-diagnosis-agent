import logging

from app.core import logging as app_logging
from app.core.logging import get_logger


def _reset_drucker_logging() -> logging.Logger:
    root = logging.getLogger("drucker")
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    root._drucker_configured = False
    return root


def test_get_logger_preserves_drucker_hierarchy():
    assert get_logger("generation").name == "drucker.generation"


def test_configure_logging_uses_one_level_for_console_and_file(tmp_path, monkeypatch, capsys):
    root = _reset_drucker_logging()
    log_file = tmp_path / "application.log"
    monkeypatch.setattr(app_logging, "APP_LOG_FILE", log_file)
    monkeypatch.setattr(app_logging, "APP_LOG_LEVEL", "INFO")
    app_logging.configure_logging()

    logger = get_logger("test")
    logger.debug("debug-only")
    logger.info("info-summary")
    console_output = capsys.readouterr().err
    file_output = log_file.read_text(encoding="utf-8")
    assert "info-summary" in console_output
    assert "debug-only" not in console_output
    assert "info-summary" in file_output
    assert "debug-only" not in file_output

    _reset_drucker_logging()
    monkeypatch.setattr(app_logging, "APP_LOG_LEVEL", "DEBUG")
    app_logging.configure_logging()
    logger.debug("debug-detail")
    console_output = capsys.readouterr().err
    file_output = log_file.read_text(encoding="utf-8")
    assert "debug-detail" in console_output
    assert "debug-detail" in file_output
    assert root.level == logging.DEBUG

    _reset_drucker_logging()


def test_console_colors_all_levels_and_file_has_no_ansi(tmp_path, monkeypatch, capsys):
    _reset_drucker_logging()
    log_file = tmp_path / "colored.log"
    monkeypatch.setattr(app_logging, "APP_LOG_FILE", log_file)
    monkeypatch.setattr(app_logging, "APP_LOG_LEVEL", "DEBUG")
    app_logging.configure_logging()

    logger = get_logger("colors")
    logger.debug("debug-summary")
    logger.info("info-summary")
    logger.warning("warning-summary")
    logger.error("error-summary")
    logger.critical("critical-summary")

    console_output = capsys.readouterr().err
    file_output = log_file.read_text(encoding="utf-8")
    for level, color in (
        ("DEBUG", "\033[96m"),
        ("INFO", "\033[92m"),
        ("WARNING", "\033[93m"),
        ("ERROR", "\033[91m"),
        ("CRITICAL", "\033[95m"),
    ):
        assert f"{color}{level}\033[0m" in console_output
    assert "\033[" not in file_output
    _reset_drucker_logging()


def test_debug_generation_logs_include_each_full_raw_response_once(tmp_path, monkeypatch):
    _reset_drucker_logging()
    log_file = tmp_path / "bounded.log"
    monkeypatch.setattr(app_logging, "APP_LOG_FILE", log_file)
    monkeypatch.setattr(app_logging, "APP_LOG_LEVEL", "DEBUG")
    app_logging.configure_logging()

    from app.tools.generation.generator import generate_diagnosis_report

    long_description = "description-" + ("D" * 2000)
    long_content = "content-" + ("C" * 2000)
    response = '{"sentences":[{"text":"' + long_content + '","source_items":[]}]} '
    outputs = iter([response] * 4)
    generate_diagnosis_report(
        description=long_description,
        problem_types=["coordination"],
        retrieved_chunks=[{"title": "chunk", "content": "R" * 2000}],
        llm=lambda messages, model: next(outputs),
    )

    logged = log_file.read_text(encoding="utf-8")
    assert long_description not in logged
    assert logged.count(response) == 4
    assert logged.count("structured generation raw_response") == 4
    assert "section=core_diagnosis model=" in logged
    assert "retrieved_items" not in logged
    _reset_drucker_logging()
