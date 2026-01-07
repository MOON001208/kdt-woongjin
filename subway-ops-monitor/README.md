# Subway Operations Monitoring Project

## Project Overview
This project monitors the real-time operations of the Seoul Subway system. It fetches data from the Seoul Data Portal API, processes it, and stores it in a Supabase (PostgreSQL) database for analysis.

## Analysis Goals (Operational Monitoring)

### 1. Real-time Train Gap Analysis
- **Objective**: Ensure trains are running at regular intervals.
- **Metric**: `Time Gap (Seconds)` = `Current Train Arrival Time` - `Previous Train Arrival Time` (at the same station).
- **Action**: Alert if the gap exceeds the threshold (e.g., > 10 mins during rush hour).

### 2. Status Distribution Monitoring
- **Objective**: Detect operational bottlenecks (e.g., trains lingering in "Arrival" state).
- **Metric**: Distribution of `train_status` (Entering vs. Arrived vs. Departed).
- **Action**: Investigate stations with high "Arrived" counts but low "Departed" counts.

### 3. Train Density Heatmap
- **Objective**: Visualize congestion by line and section.
- **Metric**: Count of active trains per Line/Section (`subway_id`, `station_id`).
- **Action**: Identify congestion hotspots.

## Folder Structure
- `main.py`: Main ETL script (Extract, Transform, Load).
- `requirements.txt`: Python package dependencies.
- `supabase/schema.sql`: Database schema definition.
- `.env`: (Not committed) Stores API Keys and Database Credentials.

## Setup
1. Create a `.env` file from `.env.example`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the ETL: `python main.py`.
