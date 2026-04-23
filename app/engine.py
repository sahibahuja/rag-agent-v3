import os
import fitz
import tempfile
from typing import List, Tuple, Dict  # Added Dict for typing
from docling.document_converter import DocumentConverter, PdfFormatOption, FormatOption # Added FormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
# FIX 1: Correct Import Path for AcceleratorOptions
from docling.datamodel.accelerator_options import AcceleratorOptions 
from docling.datamodel.base_models import InputFormat
from app.database import get_client, COLLECTION_NAME
from sentence_transformers import CrossEncoder


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

def process_file(file_path: str, metadata: dict) -> int:
    file_ext = os.path.splitext(file_path)[1].lower()
    full_markdown = ""
    
    # Resource Limits
    acc_options = AcceleratorOptions(num_threads=1) 
    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = acc_options
    pipeline_options.do_ocr = True 
    pipeline_options.do_table_structure = True
    pipeline_options.ocr_options.force_full_page_ocr = False 
    
    # FIX 2: Explicitly type the dictionary as the base class 'FormatOption' 
    # to satisfy Pylance's invariance check.
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

    # Chunking & Ingestion
    chunks = [full_markdown[i:i+1500] for i in range(0, len(full_markdown), 1200)]
    q_client = get_client()
    metadata_list = [{"source": file_path, **metadata} for _ in range(len(chunks))]
    
    q_client.add(
        collection_name=COLLECTION_NAME,
        documents=chunks,
        metadata=metadata_list
    )
    
    return len(chunks)

# --- 2. Retrieval Logic (The "Search Engine") ---

def get_context_from_qdrant(queries: List[str], limit: int = 10) -> Tuple[str, List[str]]:
    q_client = get_client()
    all_results = []

    for q in queries:
        res = q_client.query(
            collection_name=COLLECTION_NAME,
            query_text=q,
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

    for r in reranked:
        content = r.document or ""
        source = (r.metadata or {}).get("source", "Unknown Path")
        context_parts.append(f"[Source: {source}]\n{content}")
        if source not in sources:
            sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources