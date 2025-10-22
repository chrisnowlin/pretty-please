#!/usr/bin/env python3
"""
Batch RAG testing script for automated quality evaluation.

Runs a set of test queries and saves results for analysis.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_rag_interactive import RAGTester


async def batch_test(
    collection_name: str,
    queries: List[str],
    enable_reranking: bool = True,
    output_dir: str = "tests/fixtures/batch_results",
) -> List[Dict[str, Any]]:
    """
    Run batch testing on a list of queries.

    Args:
        collection_name: Collection to query
        queries: List of query strings
        enable_reranking: Whether to enable reranking
        output_dir: Directory to save results

    Returns:
        List of test results
    """
    print(f"\n{'='*80}")
    print(f"BATCH RAG TESTING")
    print(f"Collection: {collection_name}")
    print(f"Queries: {len(queries)}")
    print(f"Reranking: {'ON' if enable_reranking else 'OFF'}")
    print(f"{'='*80}\n")

    # Initialize tester
    tester = RAGTester(
        collection_name=collection_name, enable_reranking=enable_reranking
    )

    results = []
    total_time = 0

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Testing: {query[:60]}...")

        try:
            result = await tester.test_query(query, show_details=False)
            results.append(result)
            total_time += result["metrics"]["total_time_ms"]
            total_time += result["generation_time_ms"]

            # Brief summary
            citation_count = len(result["citation_map"])
            print(
                f"  ✓ Retrieved {result['metrics']['documents_after_rerank']} docs, "
                f"{citation_count} citations, "
                f"{result['metrics']['total_time_ms']:.0f}ms retrieval + "
                f"{result['generation_time_ms']:.0f}ms generation"
            )

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({"query": query, "error": str(e)})

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"batch_test_{timestamp}.json"
    filepath = output_path / filename

    with open(filepath, "w") as f:
        json.dump(
            {
                "collection": collection_name,
                "enable_reranking": enable_reranking,
                "timestamp": timestamp,
                "total_queries": len(queries),
                "total_time_ms": total_time,
                "avg_time_ms": total_time / len(queries) if queries else 0,
                "results": results,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n{'='*80}")
    print(f"BATCH TEST COMPLETE")
    print(f"Total Time: {total_time:.1f}ms")
    print(f"Avg Time: {total_time / len(queries):.1f}ms per query")
    print(f"Results saved to: {filepath}")
    print(f"{'='*80}\n")

    return results


async def main():
    """Main entry point for batch testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch RAG testing")
    parser.add_argument(
        "--collection", default="default", help="Collection name to query"
    )
    parser.add_argument(
        "--queries-file",
        required=True,
        help="Path to JSON file with test queries",
    )
    parser.add_argument(
        "--category",
        help="Specific category to test (if queries file has categories)",
    )
    parser.add_argument(
        "--no-reranking", action="store_true", help="Disable reranking"
    )
    parser.add_argument(
        "--output-dir",
        default="tests/fixtures/batch_results",
        help="Output directory for results",
    )

    args = parser.parse_args()

    # Load queries
    queries_path = Path(args.queries_file)
    if not queries_path.exists():
        print(f"Error: Queries file not found: {args.queries_file}")
        return

    with open(queries_path) as f:
        data = json.load(f)

    # Extract queries
    queries = []
    if "categories" in data and args.category:
        if args.category in data["categories"]:
            queries = data["categories"][args.category]["queries"]
        else:
            print(f"Error: Category '{args.category}' not found")
            print(f"Available categories: {list(data['categories'].keys())}")
            return
    elif "categories" in data:
        # Run all categories
        for category, info in data["categories"].items():
            queries.extend(info["queries"])
    elif "queries" in data:
        queries = data["queries"]
    else:
        print("Error: Invalid queries file format")
        return

    if not queries:
        print("Error: No queries found")
        return

    # Run batch test
    await batch_test(
        collection_name=args.collection,
        queries=queries,
        enable_reranking=not args.no_reranking,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    asyncio.run(main())
