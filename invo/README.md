# Autonomous AI Invoice Processing Worker

## Overview

An AI-powered invoice processing prototype built using Python, LangGraph, an LLM, and SQLite. The system extracts structured invoice data, validates it, pauses for human approval, and saves approved invoices to a database.

## Features

- **LLM-based extraction:** Extracts invoice ID, vendor, date, amount, and currency from invoice text files.
- **Tool calling:** Uses LangChain tools for listing, reading, extracting, and validating invoices.
- **Validation:** Checks required fields and ensures invoice amounts are numeric and positive.
- **Human-in-the-loop:** Uses LangGraph `interrupt()` and `Command(resume=...)` to pause execution until a human approves or rejects an invoice.
- **Persistent checkpoints:** Uses SQLite-backed LangGraph checkpointing to preserve workflow state.
- **Database persistence:** Stores approved invoice records in a separate SQLite database.
- **Duplicate protection:** Uses the invoice ID as a primary key to prevent duplicate records.
- **Post-save verification:** Queries SQLite to confirm that an invoice record exists.

## Architecture

1. Read the invoice text file.
2. Extract structured fields using the LLM.
3. Validate the extracted data using deterministic Python logic.
4. Pause the graph for human review.
5. Route approved invoices to the save node; end rejected workflows without saving.
6. Verify the database record after the save attempt.

## Technology Stack

- Python
- LangGraph
- LangChain
- Hugging Face model endpoint
- SQLite
- SQLite-backed LangGraph checkpointing
- Jupyter Notebook

## Database Design

Two SQLite databases are used for separate responsibilities:

- `invoice_checkpoints.db` — stores LangGraph execution checkpoints.
- `invoice_records.db` — stores invoice records and approval status.

## Testing

The prototype has been tested for:

- Invoice extraction from a real invoice file.
- Invoice field validation.
- Human approval and workflow resumption.
- Approved invoice persistence.
- Rejection routing.
- Duplicate invoice protection.
- Database record verification.
- Invalid and missing-field validation cases.

## Limitations and Future Improvements

- Add automated tests for the complete workflow and edge cases.
- Improve extraction robustness and schema validation.
- Add stronger invoice consistency checks and duplicate detection beyond invoice ID.
- Build a user interface for reviewing and approving invoices.
- Add structured logging, retry handling, and clearer database error reporting.
- Support PDF invoices and more complex invoice layouts.

## Security

Database writes are performed by a controlled Python graph node after explicit human approval. API credentials should be stored in environment variables and must not be committed to version control.

## Status

Internship-focused working prototype demonstrating LLM extraction, tool use, workflow orchestration, human approval, checkpoint persistence, and database operations.