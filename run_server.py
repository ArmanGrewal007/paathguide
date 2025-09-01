#!/usr/bin/env python3
"""Entry point for running the SGGS API server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("paathguide.api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
