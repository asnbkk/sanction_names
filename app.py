import os
import asyncio
import logging
from functools import lru_cache
from typing import List, Tuple, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from nltk.stem.snowball import SnowballStemmer

# ------------------------
# Configuration via env vars
# ------------------------
MODEL_NAME = os.getenv("MODEL_NAME", "sberbank-ai/sbert_large_nlu_ru")
TOP_N_MAX = int(os.getenv("TOP_N_MAX", "100"))

# ------------------------
# Logging
# ------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("keyword_stem_service")

# ------------------------
# FastAPI app
# ------------------------
app = FastAPI(
    title="Keyword Stemming Service",
    description="Extracts unique Russian stems from text using KeyBERT and SBERT.",
)

# ------------------------
# Models & progress tracker
# ------------------------
_embedder: SentenceTransformer | None = None
_kw_model: KeyBERT | None = None
_stemmer: SnowballStemmer | None = None
_progress: Dict[str, Any] = {"status": "not_started", "percent": 0}


# ------------------------
# Pydantic Schemas
# ------------------------
class StemRequest(BaseModel):
    doc: str = Field(..., description="Text to extract stems from.")
    top_n: int = Field(
        default=10,
        ge=1,
        le=TOP_N_MAX,
        description="Number of unique stems to return.",
    )
    min_ngram: int = Field(default=1, ge=1, description="Minimum n-gram size.")
    max_ngram: int = Field(default=1, ge=1, description="Maximum n-gram size.")

    class Config:
        schema_extra = {
            "example": {
                "doc": "Ракообразные в панцире или без панциря.",
                "top_n": 5,
                "min_ngram": 1,
                "max_ngram": 1,
            }
        }


class StemResponse(BaseModel):
    stems: List[Tuple[str, float]]


class StatusResponse(BaseModel):
    status: str
    percent: int
    details: Dict[str, Any] = {}


# ------------------------
# Startup: async model load
# ------------------------
@app.on_event("startup")
async def startup_event():
    global _embedder, _kw_model, _stemmer, _progress
    try:
        logger.info("Initializing models...")
        loop = asyncio.get_event_loop()

        _progress.update(status="loading_embedder", percent=10)
        _embedder = await loop.run_in_executor(None, SentenceTransformer, MODEL_NAME)
        logger.info("SentenceTransformer loaded")

        _progress.update(status="loading_kw_model", percent=50)
        _kw_model = await loop.run_in_executor(None, lambda: KeyBERT(model=_embedder))
        logger.info("KeyBERT model loaded")

        _progress.update(status="loading_stemmer", percent=80)
        _stemmer = SnowballStemmer("russian")
        logger.info("Stemmer initialized")

        _progress.update(status="ready", percent=100)
        logger.info("Service is ready")

    except Exception as exc:
        logger.exception("Failed to initialize models")
        _progress.update(status="error", percent=0, details={"error": str(exc)})


# ------------------------
# Dependency for ready model
# ------------------------
def get_models():
    if _progress.get("status") != "ready":
        raise HTTPException(
            status_code=503, detail="Models are loading, please try again later."
        )
    return {"kw_model": _kw_model, "stemmer": _stemmer}


# ------------------------
# Endpoints
# ------------------------
@app.get("/status", response_model=StatusResponse)
def status():
    return StatusResponse(
        status=_progress["status"],
        percent=_progress["percent"],
        details={k: v for k, v in _progress.items() if k not in ["status", "percent"]},
    )


@app.post("/extract", response_model=StemResponse)
def stems(
    request: StemRequest,
    models: Dict[str, Any] = Depends(get_models),
):
    if request.min_ngram > request.max_ngram:
        raise HTTPException(status_code=400, detail="min_ngram must be <= max_ngram")
    kw_model: KeyBERT = models["kw_model"]
    stemmer: SnowballStemmer = models["stemmer"]
    raw = kw_model.extract_keywords(
        request.doc,
        keyphrase_ngram_range=(request.min_ngram, request.max_ngram),
        top_n=request.top_n * 2,
    )
    seen = set()
    results: List[Tuple[str, float]] = []
    for word, score in raw:
        stem = stemmer.stem(word)
        if stem not in seen:
            seen.add(stem)
            results.append((stem, score))
        if len(results) >= request.top_n:
            break
    return StemResponse(stems=results)


@app.get("/health")
def health():
    return {"status": "ok"}
