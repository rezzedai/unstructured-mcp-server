"""Unstructured SDK/API wrapper for document partitioning."""

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger("unstructured-mcp")

UNSTRUCTURED_API_KEY = os.environ.get("UNSTRUCTURED_API_KEY")
UNSTRUCTURED_API_URL = os.environ.get(
    "UNSTRUCTURED_API_URL", "https://api.unstructuredapp.io/general/v0/general"
)


@dataclass
class PartitionResult:
    elements: list[dict] = field(default_factory=list)
    strategy_used: str = "auto"


def _element_to_dict(element) -> dict:
    """Convert an Unstructured Element to a serializable dict."""
    result = {
        "type": type(element).__name__,
        "text": str(element),
    }
    if hasattr(element, "metadata"):
        meta = element.metadata
        meta_dict = {}
        for attr in ("page_number", "filename", "coordinates", "parent_id", "text_as_html"):
            val = getattr(meta, attr, None)
            if val is not None:
                meta_dict[attr] = val
        result["metadata"] = meta_dict
    return result


def _partition_local(file_path: str, strategy: str) -> list:
    """Partition using the local unstructured package."""
    from unstructured.partition.auto import partition as unstructured_partition

    return unstructured_partition(filename=file_path, strategy=strategy)


def _partition_api(file_path: str, strategy: str) -> list:
    """Partition using the Unstructured hosted API."""
    from unstructured_client import UnstructuredClient
    from unstructured_client.models import operations, shared

    client = UnstructuredClient(
        api_key_auth=UNSTRUCTURED_API_KEY,
        server_url=UNSTRUCTURED_API_URL,
    )

    with open(file_path, "rb") as f:
        file_content = f.read()

    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(
            files=shared.Files(
                content=file_content,
                file_name=os.path.basename(file_path),
            ),
            strategy=shared.Strategy(strategy),
        ),
    )

    resp = client.general.partition(request=req)
    return resp.elements or []


def _detect_strategy(file_path: str, requested: str) -> str:
    """Auto-detect the best strategy based on file characteristics."""
    if requested != "auto":
        return requested

    ext = os.path.splitext(file_path)[1].lower()
    # Use hi_res for images and scanned PDFs — fast for everything else
    if ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        logger.info("Auto-detected image file — using hi_res strategy")
        return "hi_res"

    # For PDFs, check if it's likely scanned (small text layer)
    if ext == ".pdf":
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            # Heuristic: large PDFs with few pages are often scanned
            if size_mb > 5:
                logger.info("Large PDF (%.1fMB) — using hi_res strategy", size_mb)
                return "hi_res"
        except OSError:
            pass

    return "fast"


def partition(file_path: str, strategy: str = "auto") -> PartitionResult:
    """Partition a document into structured elements.

    Uses the Unstructured API if UNSTRUCTURED_API_KEY is set,
    otherwise falls back to local processing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    effective_strategy = _detect_strategy(file_path, strategy)
    use_api = bool(UNSTRUCTURED_API_KEY)

    logger.info(
        "Partitioning %s (strategy=%s, mode=%s)",
        os.path.basename(file_path),
        effective_strategy,
        "api" if use_api else "local",
    )

    if use_api:
        raw_elements = _partition_api(file_path, effective_strategy)
        # API returns dicts already
        elements = []
        for el in raw_elements:
            if isinstance(el, dict):
                elements.append(el)
            else:
                elements.append(_element_to_dict(el))
    else:
        raw_elements = _partition_local(file_path, effective_strategy)
        elements = [_element_to_dict(el) for el in raw_elements]

    return PartitionResult(elements=elements, strategy_used=effective_strategy)
