# Graduate Data Analysis System

## Overview

This is a comprehensive graduate school application data analysis system that scrapes and analyzes applicant information from The Grad Cafe website. The system provides a Flask-based web interface for viewing statistical insights about graduate program applications, acceptance rates, GPA trends, and demographic patterns. It consists of a data pipeline that collects, cleans, and enriches applicant data using both web scraping and LLM-based standardization, stores it in a PostgreSQL database, and presents analytical results through an interactive web dashboard.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Data Collection Pipeline
The system implements a multi-stage data collection and processing pipeline:
- **Web Scraping**: Automated extraction of new applicant data from The Grad Cafe using BeautifulSoup and urllib3
- **Data Cleaning**: Standardization of inconsistent data formats, handling of missing values, and data validation
- **LLM Enhancement**: Local TinyLlama model integration for standardizing program names and university names to canonical forms
- **Incremental Updates**: Smart detection of new entries to avoid duplicate data processing

### Database Architecture
- **PostgreSQL Backend**: Centralized data storage using psycopg for database connectivity
- **Schema Design**: Single `applicants` table with fields including program, university, application status, GPA, GRE scores, demographic information, and LLM-generated standardized fields
- **Data Integrity**: Handles duplicate detection and manages data consistency across updates

### Web Application Framework
- **Flask Framework**: Lightweight Python web framework serving the analysis dashboard
- **Blueprint Architecture**: Modular route organization separating concerns between application logic and page rendering
- **Template System**: Jinja2 templating for dynamic content rendering with Bootstrap-style responsive design
- **Static Assets**: Custom CSS styling with button-based interaction patterns

### Query and Analytics Engine
- **Predefined Analytics**: Set of 10 analytical queries covering application volume, acceptance rates, demographic breakdowns, and institutional comparisons
- **Real-time Data**: Dynamic query execution against current database state
- **Statistical Calculations**: Percentage calculations, averages, and comparative analysis with proper formatting

### LLM Integration Service
- **Local Model Hosting**: Self-contained Flask API service running TinyLlama 1.1B model via llama-cpp-python
- **Standardization Logic**: Canonical university and program name matching with fuzzy string matching fallbacks
- **Resource Management**: CPU-optimized configuration suitable for Replit deployment with configurable model parameters

## Deployment and Configuration

### Environment Variables
The application uses environment variables for flexible deployment across different platforms:
- **DATABASE_URL** (required): PostgreSQL connection string
- **HOST** (optional): Bind address - defaults to 0.0.0.0 for cloud/network access, set to 127.0.0.1 for local-only access
- **PORT** (optional): Server port - defaults to 5000 for main app, 8000 for LLM service
- **FLASK_DEBUG** (optional): Enable debug mode (True/False)
- **SECRET_KEY** (optional): Flask session secret key

### Platform Support
- **Cloud Deployment (Replit)**: Works out-of-the-box with default configuration (HOST=0.0.0.0, PORT=5000)
- **Local Windows Development**: Fully supported with optional HOST=127.0.0.1 configuration for local-only access
- **VS Code Integration**: Compatible with VS Code debugging and development workflows

### Setup Files
- **.env.example**: Template with all environment variables and explanations
- **WINDOWS_SETUP.md**: Complete step-by-step setup guide for Windows users including PostgreSQL installation and configuration

## External Dependencies

### Core Infrastructure
- **PostgreSQL Database**: Primary data storage accessed via DATABASE_URL environment variable
- **Multi-platform Support**: Runs on Replit cloud hosting, Windows local machines, and other environments

### Third-Party Services
- **The Grad Cafe**: External data source for graduate application information via web scraping
- **Hugging Face Hub**: Model repository for downloading TinyLlama GGUF model files

### Python Libraries
- **Database**: psycopg for PostgreSQL connectivity
- **Web Framework**: Flask, Jinja2 for web application and templating
- **Data Processing**: BeautifulSoup4, urllib3 for web scraping and HTTP requests
- **LLM Processing**: llama-cpp-python for local language model inference
- **Testing**: pytest for comprehensive test coverage including unit, integration, and end-to-end tests
- **Documentation**: Sphinx with Read the Docs theme for API documentation generation

### Development Tools
- **Testing Framework**: pytest with fixtures and mocking for 86% code coverage
- **Documentation**: Sphinx autodoc for automatic API documentation generation
- **Code Organization**: Modular structure with separate concerns for data loading, querying, updating, and web presentation