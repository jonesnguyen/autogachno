import logging

# Thin entrypoint that reuses the existing main until full refactor is completed
from .main import main as _legacy_main


def main() -> None:
    logging.getLogger(__name__).info("Starting application via app.app.main (delegating to legacy main)")
    _legacy_main()


if __name__ == "__main__":
    main()


