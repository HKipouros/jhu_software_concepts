# Windows Setup Guide

This guide will help you set up and run the Graduate Data Analysis System on your Windows machine using VS Code.

## Prerequisites

1. **Python 3.11 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **PostgreSQL Database**
   - Download from [postgresql.org](https://www.postgresql.org/download/windows/)
   - Remember the password you set for the `postgres` user during installation

3. **VS Code** (optional but recommended)
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)
   - Install the Python extension

## Step 1: Clone/Download the Project

Download this project to your local machine and open it in VS Code.

## Step 2: Set Up PostgreSQL Database

1. Open **pgAdmin** (installed with PostgreSQL) or use **psql** command line
2. Create a new database:
   ```sql
   CREATE DATABASE gradcafe_db;
   ```

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` file with your settings:
   - Update `DATABASE_URL` with your PostgreSQL credentials
   - Default username is usually `postgres`
   - Use the password you set during PostgreSQL installation
   - Example: `postgresql://postgres:mypassword@localhost:5432/gradcafe_db`
   - **Optional for local-only access**: Uncomment `HOST=127.0.0.1` to restrict access to your machine only
   - By default, HOST is set to `0.0.0.0` which allows network access (useful for testing on other devices)

## Step 4: Install Python Dependencies

Open a terminal in VS Code (Terminal → New Terminal) and run:

```bash
pip install -r requirements.txt
```

Or if you prefer using the project configuration:

```bash
pip install -e .
```

## Step 5: Initialize the Database

The database schema will be created automatically when you first run the data loading scripts, or you can manually create it using the SQL schema if provided.

## Step 6: Run the Application

### Option A: Using Python directly
```bash
python src/website/app.py
```

### Option B: Using VS Code Debugger
1. Press F5 or go to Run → Start Debugging
2. Select "Python File"
3. The app will start and you can access it at: http://127.0.0.1:5000

## Step 7: Access the Application

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL service is running (check Windows Services)
- Confirm your DATABASE_URL is correct in `.env`
- Test connection using pgAdmin or psql

### Port Already in Use
- Change the PORT in `.env` to another number (e.g., 8000)
- Or stop the process using port 5000

### Import Errors
- Make sure you're in the project root directory
- Verify all dependencies are installed: `pip list`
- Try reinstalling: `pip install -r requirements.txt --force-reinstall`

### Python Path Issues
- Ensure Python is added to your Windows PATH
- Try using `python3` instead of `python` if needed

## Optional: Load Sample Data

If you want to populate the database with data from The Grad Cafe:

```bash
python src/load_data.py
```

This will scrape recent data and store it in your database.

## Development Tips

1. **Enable Debug Mode**: Set `FLASK_DEBUG=True` in `.env` for auto-reload during development
2. **Use Virtual Environment**: 
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Database GUI**: Use pgAdmin or DBeaver to view your PostgreSQL data

## Next Steps

- Explore the web interface at http://127.0.0.1:5000
- Check the analytics queries in the dashboard
- Modify the code to suit your needs
- Review the project documentation in `replit.md`

## Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Ensure PostgreSQL is running and accessible
4. Check that all dependencies are installed
