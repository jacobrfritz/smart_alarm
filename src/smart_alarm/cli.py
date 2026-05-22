import argparse
import logging
import sys

from .config import Config, load_dotenv
from .main import run_alarm


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parses command-line arguments for the Sonos Math Alarm CLI."""
    parser = argparse.ArgumentParser(
        description="Sonos Math Alarm Command Line Interface"
    )
    parser.add_argument(
        "--config",
        default=".env",
        help="Path to the .env file containing connection/credentials configuration (default: .env)",
    )
    return parser.parse_args(args)


def main() -> None:
    """Entry point for the CLI script."""
    # Setup readable logging output to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    args = parse_args(sys.argv[1:])

    # Load custom dot env file if provided
    load_dotenv(args.config)

    # Initialize configuration
    config = Config()

    try:
        # Validate that credentials and emails are configured
        config.validate()
    except ValueError as e:
        logging.critical(f"Configuration validation failed: {e}")
        sys.exit(1)

    logging.info("Starting Sonos Math Alarm...")
    try:
        # Execute the alarm orchestrator
        success = run_alarm(config)
        if success:
            logging.info(
                "Alarm process terminated: Correct reply answered successfully."
            )
            sys.exit(0)
        else:
            logging.error("Alarm process terminated: Predefined alarm timeout elapsed.")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Alarm process manually aborted by user (SIGINT). Exiting.")
        sys.exit(0)
    except Exception as ex:
        logging.critical(
            f"Fatal unhandled exception in alarm controller thread: {ex}", exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
