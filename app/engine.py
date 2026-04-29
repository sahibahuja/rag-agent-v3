import os
import fitz
import tempfile
from typing import List, Tuple, Dict  
from docling.document_converter import DocumentConverter, PdfFormatOption, FormatOption 
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions 
from docling.datamodel.base_models import InputFormat
import uuid
from app.database import get_client, COLLECTION_NAME, PARENT_COLLECTION_NAME
from sentence_transformers import CrossEncoder

# NEW IMPORT: Needed for the Multi-Tenancy filtering
from qdrant_client.http import models 

_reranker = None

def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("BAAI/bge-reranker-base")
    return _reranker

def rerank_results(query: str, results: list, top_k: int = 4):
    if not results:
        return []

    try:
        reranker = get_reranker()
        pairs = [(query, r.document or "") for r in results]
        scores = reranker.predict(pairs)

        scored = list(zip(results, scores))
        scored.sort(key=lambda x: float(x[1]), reverse=True)

        return [item[0] for item in scored[:top_k]]
    except Exception as e:
        print(f"⚠️ Reranker failed, using original order: {e}")
        return results[:top_k]

# FIX: Added tenant_id as a required parameter to enforce security at ingestion
def process_file(file_path: str, metadata: dict, tenant_id: str) -> int:
    file_ext = os.path.splitext(file_path)[1].lower()
    full_markdown = ""
    
    # Resource Limits
    acc_options = AcceleratorOptions(num_threads=1) 
    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = acc_options
    pipeline_options.do_ocr = True 
    pipeline_options.do_table_structure = True
    pipeline_options.ocr_options.force_full_page_ocr = False 
    
    format_options: Dict[InputFormat, FormatOption] = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
    
    converter = DocumentConverter(format_options=format_options)

    if file_ext == ".pdf":
        doc = fitz.open(file_path)
        total_pages = len(doc)
        chunk_size = 10 

        for i in range(0, total_pages, chunk_size):
            start_page = i
            end_page = min(i + chunk_size, total_pages)
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf_path = tmp.name
                
            try:
                temp_doc = fitz.open()
                temp_doc.insert_pdf(doc, from_page=start_page, to_page=end_page-1)
                temp_doc.save(temp_pdf_path)
                temp_doc.close()

                result = converter.convert(temp_pdf_path)
                full_markdown += result.document.export_to_markdown() + "\n\n"
            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
        doc.close()
    else:
        result = converter.convert(file_path)
        full_markdown = result.document.export_to_markdown()

    # --- Parent-Child Chunking Strategy ---
    parent_size = 3000 
    parent_overlap = 500
    parent_chunks = [full_markdown[i:i+parent_size] for i in range(0, len(full_markdown), parent_size - parent_overlap)]
    
    q_client = get_client()
    child_chunks = []
    child_metadata = []
    
    parent_storage_ids = []
    parent_storage_payloads = []

    for p_text in parent_chunks:
        parent_id = str(uuid.uuid4())
        
        # 2. Store Parent with tenant_id
        parent_storage_ids.append(parent_id)
        parent_storage_payloads.append({
            "text": p_text,
            "source": file_path,
            "tenant_id": tenant_id,  # <-- SECURE ISOLATION
            **metadata
        })

        # 3. Generate Child Chunks
        child_size = 600 
        child_overlap = 100
        p_children = [p_text[j:j+child_size] for j in range(0, len(p_text), child_size - child_overlap)]
        
        for c_text in p_children:
            child_chunks.append(c_text)
            child_metadata.append({
                "source": file_path,
                "parent_id": parent_id,
                "tenant_id": tenant_id,  # <-- SECURE ISOLATION
                **metadata
            })

    # 4. Batch Upload Parents
    from qdrant_client.http.models import PointStruct
    q_client.upsert(
        collection_name=PARENT_COLLECTION_NAME,
        points=[
            PointStruct(
                id=pid,
                vector={}, # No vector for parent
                payload=payload
            ) for pid, payload in zip(parent_storage_ids, parent_storage_payloads)
        ]
    )

    # 5. Batch Upload Children
    q_client.add(
        collection_name=COLLECTION_NAME,
        documents=child_chunks,
        metadata=child_metadata
    )
    
    return len(child_chunks)

# --- 2. Retrieval Logic (The "Search Engine") ---

# FIX: Added tenant_id to signature
def get_context_from_qdrant(queries: List[str], tenant_id: str, limit: int = 10) -> Tuple[str, List[str]]:
    q_client = get_client()
    all_results = []

    # --- THE SECURITY WALL (Point 6) ---
    tenant_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id),
            )
        ]
    )

    for q in queries:
        res = q_client.query(
            collection_name=COLLECTION_NAME,
            query_text=q,
            query_filter=tenant_filter, # <-- APPLIED FILTER HERE
            limit=limit
        )
        all_results.extend(res)

    # dedupe by document text
    unique_by_doc = {}
    for r in all_results:
        doc = r.document or ""
        if doc and doc not in unique_by_doc:
            unique_by_doc[doc] = r

    deduped_results = list(unique_by_doc.values())

    # rerank using first query as anchor
    anchor_query = queries[0] if queries else ""
    reranked = rerank_results(anchor_query, deduped_results, top_k=4)

    context_parts = []
    sources = []

    # --- Auto-Merging: Fetch Parent Text ---
    for r in reranked:
        metadata = r.metadata or {}
        parent_id = metadata.get("parent_id")
        source = metadata.get("source", "Unknown Path")
        
        if parent_id:
            try:
                # We can also add tenant filtering here, but since parent_id is UUID 
                # and came from a tenant-filtered child, it's inherently secure.
                parent_docs = q_client.retrieve(
                    collection_name=PARENT_COLLECTION_NAME,
                    ids=[parent_id]
                )
                if parent_docs and parent_docs[0].payload:
                    content = parent_docs[0].payload.get("text", r.document or "")
                else:
                    content = r.document or ""
            except Exception as e:
                print(f"⚠️ Failed to fetch parent {parent_id}: {e}")
                content = r.document or ""
        else:
            content = r.document or ""

        context_parts.append(f"[Source: {source}]\n{content}")
        if source not in sources:
            sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources