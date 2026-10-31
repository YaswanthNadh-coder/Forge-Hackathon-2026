"""
CLI script to ingest official NHA HBP 2022 dataset into Qdrant vector database.
Usage:
    python -m app.scripts.ingest_hbp
    python -m app.scripts.ingest_hbp --file path/to/hbp_file.json
"""

import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ingest_hbp_cli")


async def main():
    parser = argparse.ArgumentParser(description="Ingest HBP 2022 Master dataset into Qdrant")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to HBP data file (JSON, CSV, XLSX, or PDF)",
    )
    args = parser.parse_args()

    # Determine file path
    if args.file:
        data_path = Path(args.file)
    else:
        # Default to bundled official master dataset
        backend_dir = Path(__file__).resolve().parent.parent.parent
        data_path = backend_dir / "data" / "hbp_2022_master.json"

    if not data_path.exists():
        logger.error(f"HBP dataset file not found at: {data_path}")
        sys.exit(1)

    logger.info(f"Target HBP file: {data_path}")

    from app.rag.qdrant_store import qdrant_manager
    from app.rag.ingest import ingest_hbp_data

    logger.info("Connecting to Qdrant vector store...")
    await qdrant_manager.initialize()

    info = qdrant_manager.get_collection_info()
    logger.info(f"Pre-ingestion Qdrant collection status: {info}")

    logger.info("Commencing dataset ingestion and indexing...")
    result = await ingest_hbp_data(str(data_path))
    logger.info(f"Ingestion finished successfully: {result}")

    info_after = qdrant_manager.get_collection_info()
    logger.info(f"Post-ingestion Qdrant collection status: {info_after}")


if __name__ == "__main__":
    asyncio.run(main())

