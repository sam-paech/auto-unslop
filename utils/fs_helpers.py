import nltk
import datetime
from pathlib import Path
import logging
import sys
import shutil # For copying config example

logger = logging.getLogger(__name__)

def download_nltk_resource(resource_id: str, resource_name: str):
    """Downloads NLTK resource if not found."""
    try:
        nltk.data.find(resource_id)
        logger.debug(f"NLTK '{resource_name}' resource found.")
    except LookupError:
        logger.info(f"NLTK '{resource_name}' resource not found. Downloading...")
        try:
            nltk.download(resource_name, quiet=True)
            logger.info(f"NLTK '{resource_name}' resource downloaded.")
        except Exception as e:
            logger.warning(f"Could not automatically download NLTK '{resource_name}' resource: {e}. "
                           "Manual download might be required (e.g., python -m nltk.downloader punkt stopwords)")
    except Exception as e:
        logger.warning(f"Error checking NLTK '{resource_name}' resource: {e}.")

def create_experiment_dir(base_dir_path: Path, resume_dir: Path | None = None) -> Path:
    """
    Determine the directory that the pipeline should work in.

    • When --resume-from-dir is supplied we MUST use that exact path.
      If the directory is missing or not a directory, raise immediately.

    • When no resume dir is given, create a new timestamped directory under
      *base_dir_path* (parents created as needed) and return it.
    """
    if resume_dir is not None:
        if resume_dir.is_dir():
            logger.info(f"Resuming experiment in existing directory: {resume_dir.resolve()}")
            return resume_dir
        # hard-fail: the user explicitly asked to resume here
        raise FileNotFoundError(
            f"--resume-from-dir was set to '{resume_dir}', "
            "but that path does not exist or is not a directory."
        )

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_dir = base_dir_path / f"run_{timestamp}"
    experiment_dir.mkdir(parents=True, exist_ok=False)
    logger.info(f"Created experiment directory: {experiment_dir.resolve()}")
    return experiment_dir


def ensure_antislop_vllm_config_exists(antislop_vllm_dir: Path):
    """
    Copies antislop-vllm/config-example.yaml to config.yaml if config.yaml is absent.
    This is a helper for users, but the main pipeline will pass params via CLI.
    """
    cfg_path = antislop_vllm_dir / "config.yaml"
    example_path = antislop_vllm_dir / "config-example.yaml"

    if not cfg_path.exists():
        if example_path.exists():
            try:
                shutil.copy(example_path, cfg_path)
                logger.info(f"Copied {example_path} to {cfg_path} for antislop-vllm (user convenience).")
            except Exception as e:
                logger.warning(f"Could not copy antislop-vllm config example: {e}")
        else:
            logger.debug("antislop-vllm/config-example.yaml not found. No default config.yaml created for it.")
    else:
        logger.debug("antislop-vllm/config.yaml already exists.")


###############################################################################
# NLTK helpers
###############################################################################
CORE_NLTK_RESOURCES = [
    ("tokenizers/punkt",       "punkt"),        # sentence + word tokeniser data
    ("tokenizers/punkt_tab",   "punkt_tab"),    # new in NLTK 3.9+, used by PunktTokenizer
    ("corpora/stopwords",      "stopwords"),    # obvious
]

def ensure_core_nltk_resources() -> None:
    """
    Download the three NLTK resources our pipeline needs *once* at start-up.
    Safe to call multiple times – it‘s a no-op if they’re already present.
    """
    for resource_id, resource_name in CORE_NLTK_RESOURCES:
        download_nltk_resource(resource_id, resource_name)
