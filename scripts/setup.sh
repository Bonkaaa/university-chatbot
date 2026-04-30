#!/bin/bash

echo "Setting up the directory structure for the project..."
python setup_dir.py

echo "Scraping data from the web..."
python -m src.rag_core.components.data_ingestion.scraper

echo "Initializing the database for retriever..."
python -m src.rag_core.components.data_ingestion.document_loaders

echo "Done"