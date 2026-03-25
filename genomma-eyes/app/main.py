"""
Genomma Eyes - Inteligencia colectiva de punto de venta.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Genomma Eyes",
    description="Plataforma de inteligencia colectiva de punto de venta para Genomma Lab",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)


@app.get("/")
async def root():
    return {"status": "ok", "app": "Genomma Eyes 👁️", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
