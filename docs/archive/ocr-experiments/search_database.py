#!/usr/bin/env python3
"""Search persisted documents in the database.

This script allows you to search for content in documents that have been
processed and persisted to the ChromaVectorStore database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.storage import ChromaVectorStore
from jina_rag_pipeline.embeddings import JinaEmbeddings


def search_collection(
    query: str,
    collection_name: str = "teach_like_champion_3_full",
    top_k: int = 5,
    db_path: str = "./db"
) -> None:
    """Search a collection in the database.

    Args:
        query: Search query text
        collection_name: Name of collection to search
        top_k: Number of top results to return
        db_path: Path to database directory
    """
    print("\n" + "=" * 80)
    print("DOCUMENT SEARCH")
    print("=" * 80)
    print(f"Collection: {collection_name}")
    print(f"Query: {query}")
    print(f"Top results: {top_k}")
    print("=" * 80 + "\n")

    try:
        # Initialize
        vector_store = ChromaVectorStore(persist_directory=db_path)
        embedder = JinaEmbeddings(model_name="jina-embeddings-v4")

        # List collections
        collections = vector_store.list_collections()
        print(f"Available collections ({len(collections)}):")
        for col in collections:
            print(f"  - {col.name}: {col.count} embeddings")
        print()

        # Check if collection exists
        collection_names = [c.name for c in collections]
        if collection_name not in collection_names:
            print(f"❌ Collection '{collection_name}' not found in database")
            print(f"Available collections: {collection_names}")
            vector_store.close()
            return

        # Generate embedding for query (2048-dim to match stored embeddings)
        print(f"Embedding query...")
        query_embedding = embedder.embed_text(query, truncate_dim=2048)

        # Search
        print(f"Searching {collection_name}...")
        results = vector_store.similarity_search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=top_k
        )

        if not results:
            print("❌ No results found")
            vector_store.close()
            return

        print(f"✅ Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.metadata.get('region_type', 'text')}] "
                  f"(Score: {result.score:.3f}, Page: {result.metadata.get('page_number', '?')})")
            print(f"   Document: {Path(result.metadata.get('source', 'unknown')).name}")

            # Show snippet
            content_preview = result.document[:200].replace('\n', ' ')
            if len(result.document) > 200:
                content_preview += "..."
            print(f"   {content_preview}")
            print()

        vector_store.close()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def list_collections(db_path: str = "./db") -> None:
    """List all collections in the database."""
    print("\n" + "=" * 80)
    print("DATABASE COLLECTIONS")
    print("=" * 80 + "\n")

    try:
        vector_store = ChromaVectorStore(persist_directory=db_path)
        collections = vector_store.list_collections()

        if not collections:
            print("No collections found in database")
            vector_store.close()
            return

        for col in collections:
            stats = vector_store.get_collection_stats(col.name)
            print(f"Collection: {col.name}")
            print(f"  Embeddings: {stats.count}")
            print(f"  Metadata: {stats.metadata}")
            print()

        vector_store.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_collections()
        else:
            # Search with provided query
            query = " ".join(sys.argv[1:])
            search_collection(query)
    else:
        print("Usage:")
        print("  python search_database.py <query>          - Search the database")
        print("  python search_database.py --list           - List all collections")
        print()
        print("Examples:")
        print("  python search_database.py 'teaching strategies'")
        print("  python search_database.py 'assessment methods'")
        print("  python search_database.py --list")
