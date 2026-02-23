# RJ ETL Pipeline - Complete Installation Guide

Comprehensive step-by-step installation for Windows, macOS, and Linux

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Windows Installation](#windows-installation)
3. [macOS Installation](#macos-installation)
4. [Linux Installation](#linux-installation)
5. [Common Installation Issues](#common-installation-issues)
6. [Verification & Testing](#verification--testing)

---

## System Requirements

### Minimum
- **CPU**: Dual-core processor
- **RAM**: 4 GB (8+ GB recommended for batch processing)
- **Disk Space**: 500 MB for application + adequate space for database
- **Network**: Connection to PostgreSQL database
- **Python**: 3.8 or higher

### Recommended
- **CPU**: Quad-core or better
- **RAM**: 8+ GB (batch processing is memory-intensive)
- **Disk Space**: 1+ GB for logs and temporary files
- **Database**: Dedicated PostgreSQL 12+ server or managed service

### Software Prerequisites
- PostgreSQL 12+ (or PostgreSQL 15+ recommended)
- Python 3.8+ (Python 3.11 recommended)
- pip package manager
- Git (optional, for downloading repository)

---

## Windows Installation

### Step 1: Install PostgreSQL on Windows

#### Option A: PostgreSQL Installer (Recommended)

1. Download from https://www.postgresql.org/download/windows/
2. Run the installer (choose version 15 or higher)
3. During installation:
   - **Installation Directory**: `C:\Program Files\PostgreSQL\15`
   - **Data Directory**: `C:\Program Files\PostgreSQL\15\data`
   - **Port**: 5432 (default)
   - **Superuser**: postgres
   - **Password**: Choose a strong password and save it
   - **Locale**: English

4. When installation completes:
   - Select "Stack Builder" if you want additional tools (optional)
   - Finish installation

5. Verify installation:
   ```powershell
   # Open PowerShell and check
   psql --version
   # Should output: psql (PostgreSQL) 15.x
   ```

#### Option B: PostgreSQL Windows Service

PostgreSQL should automatically start as a Windows service. To verify:

1. Open Services:
   - Press `Win + R`
   - Type `services.msc`
   - Look for "postgresql-x64-15" (running status)

2. If not running, right-click and select "Start"

### Step 2: Create Database and User

Open PowerShell and connect to PostgreSQL:

```powershell
# Connect as superuser
psql -U postgres

# In psql prompt, create database and user:
CREATE DATABASE rj_hotel;
CREATE USER rj_etl_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE rj_hotel TO rj_etl_user;
\q
```

### Step 3: Install Python

1. Download from https://www.python.org/downloads/windows/
2. Run installer (choose Python 3.11 or higher)
3. **IMPORTANT**: Check "Add Python to PATH"
4. Choose "Install Now"

Verify installation:
```powershell
python --version
# Should show Python 3.11.x or higher

pip --version
# Should show pip 22.x or higher
```

### Step 4: Install RJ ETL Pipeline

Create a working directory:
```powershell
# Create folder
mkdir C:\RJ_ETL_Pipeline
cd C:\RJ_ETL_Pipeline

# Clone or download files (example using git)
git clone <repository-url> .

# Or extract downloaded ZIP file
```

Install Python dependencies:
```powershell
# Navigate to project directory
cd C:\RJ_ETL_Pipeline

# Install requirements
pip install -r etl_requirements.txt

# Verify installations
python -c "import xlrd; print('xlrd OK')"
python -c "import psycopg2; print('psycopg2 OK')"
```

### Step 5: Configure Database Connection

Edit `db_config.json` in the project directory:

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user",
  "password": "secure_password_here",
  "schema": "rj_data"
}
```

### Step 6: Create Database Schema

```powershell
# Run the setup script
python setup.py

# Or run schema directly with psql
psql -U rj_etl_user -d rj_hotel -f database_schema.sql
```

### Step 7: Test Installation

```powershell
# Run validation
python validate_data.py --config db_config.json

# Expected output shows database connection success
```

---

## macOS Installation

### Step 1: Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install PostgreSQL

Using Homebrew (recommended):
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
# Should output: psql (PostgreSQL) 15.x
```

Or using MacPorts:
```bash
sudo port install postgresql15-server
```

Or using Docker:
```bash
docker pull postgres:15
docker run -d --name rj_postgres \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:15
```

### Step 3: Create Database and User

```bash
# Connect as superuser
psql -U postgres

# In psql prompt:
CREATE DATABASE rj_hotel;
CREATE USER rj_etl_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE rj_hotel TO rj_etl_user;
\q
```

### Step 4: Install Python

Using Homebrew:
```bash
# Install Python
brew install python@3.11

# Verify
python3 --version
pip3 --version
```

Or using MacPorts:
```bash
sudo port install python311
```

### Step 5: Install RJ ETL Pipeline

```bash
# Create working directory
mkdir -p ~/Projects/RJ_ETL_Pipeline
cd ~/Projects/RJ_ETL_Pipeline

# Clone or download files
git clone <repository-url> .

# Install Python dependencies
pip3 install -r etl_requirements.txt

# Verify
python3 -c "import xlrd; print('xlrd OK')"
python3 -c "import psycopg2; print('psycopg2 OK')"
```

### Step 6: Configure Database Connection

```bash
# Edit configuration
nano db_config.json
```

Content:
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user",
  "password": "secure_password_here",
  "schema": "rj_data"
}
```

### Step 7: Create Database Schema

```bash
# Run setup script
python3 setup.py

# Or manually with psql
psql -U rj_etl_user -d rj_hotel -f database_schema.sql
```

### Step 8: Test Installation

```bash
python3 validate_data.py --config db_config.json
```

### macOS: Make Scripts Executable

```bash
chmod +x rj_etl_pipeline.py
chmod +x process_batch.sh
chmod +x validate_data.py
chmod +x setup.py
```

---

## Linux Installation

### Step 1: Install PostgreSQL

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-dev

# Verify
psql --version
```

#### CentOS/RHEL:
```bash
# Install PostgreSQL repository
sudo yum install https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL
sudo yum install postgresql15-server postgresql15-contrib postgresql15-devel

# Initialize database
sudo /usr/pdbv/15/bin/postgresql-15-setup initdb

# Start service
sudo systemctl start postgresql-15
sudo systemctl enable postgresql-15
```

### Step 2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In psql prompt:
CREATE DATABASE rj_hotel;
CREATE USER rj_etl_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE rj_hotel TO rj_etl_user;
\q
```

### Step 3: Install Python

#### Ubuntu/Debian:
```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3 python3-pip python3-dev python3-venv

# Verify
python3 --version
pip3 --version
```

#### CentOS/RHEL:
```bash
# Install Python 3.11
sudo yum install python3.11 python3.11-pip python3.11-devel

# Verify
python3.11 --version
```

### Step 4: Install RJ ETL Pipeline

```bash
# Create working directory
mkdir -p ~/rj_etl_pipeline
cd ~/rj_etl_pipeline

# Clone repository
git clone <repository-url> .

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r etl_requirements.txt

# Verify
python -c "import xlrd; print('xlrd OK')"
python -c "import psycopg2; print('psycopg2 OK')"
```

### Step 5: Configure Database Connection

```bash
# Edit configuration file
nano db_config.json
```

Content:
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user",
  "password": "secure_password_here",
  "schema": "rj_data"
}
```

### Step 6: Create Database Schema

```bash
# Using setup script
python setup.py

# Or manually
psql -U rj_etl_user -d rj_hotel -f database_schema.sql
```

### Step 7: Make Scripts Executable

```bash
chmod +x rj_etl_pipeline.py
chmod +x process_batch.sh
chmod +x validate_data.py
chmod +x setup.py
```

### Step 8: Set Up Permissions

Create an unprivileged user for running ETL (optional but recommended):

```bash
# Create system user
sudo useradd -m -s /bin/bash rj_etl

# Create data directory
sudo mkdir -p /var/rj_etl_data
sudo chown rj_etl:rj_etl /var/rj_etl_data

# Copy application files
sudo cp -r ~/rj_etl_pipeline /home/rj_etl/
sudo chown -R rj_etl:rj_etl /home/rj_etl/rj_etl_pipeline

# Test as new user
sudo -u rj_etl python3 validate_data.py
```

---

## Cloud Database Installation

### AWS RDS PostgreSQL

1. Create RDS instance via AWS console
2. Note endpoint: `rj-database.xxxxx.us-east-1.rds.amazonaws.com`
3. Configure `db_config.json`:

```json
{
  "host": "rj-database.xxxxx.us-east-1.rds.amazonaws.com",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user",
  "password": "your-secure-password",
  "schema": "rj_data"
}
```

### Azure Database for PostgreSQL

1. Create instance via Azure portal
2. Note server name: `rj-database.postgres.database.azure.com`
3. Configure:

```json
{
  "host": "rj-database.postgres.database.azure.com",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user@rj-database",
  "password": "your-secure-password",
  "schema": "rj_data"
}
```

---

## Common Installation Issues

### Issue 1: PostgreSQL Connection Refused

**Windows:**
```powershell
# Check service status
Get-Service postgresql*

# If not running, start it
Start-Service postgresql-x64-15

# Or in Services.msc
```

**macOS/Linux:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Check if PostgreSQL is listening
sudo netstat -tlnp | grep 5432
```

### Issue 2: Python Not Found

**Windows:**
- Add Python to PATH: Edit environment variables
- Restart PowerShell after adding to PATH
- Use full path: `C:\Python311\python.exe`

**macOS/Linux:**
```bash
# Use python3 instead of python
python3 --version

# Or create alias
alias python=python3
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

### Issue 3: Permission Denied

**Linux/macOS:**
```bash
# Make scripts executable
chmod +x *.py
chmod +x *.sh

# Check permissions
ls -la rj_etl_pipeline.py
# Should show: -rwxr-xr-x

# If still issues, use explicit python
python3 rj_etl_pipeline.py
```

### Issue 4: Module Not Found

```bash
# Ensure pip is upgraded
python -m pip install --upgrade pip

# Reinstall requirements
pip install --force-reinstall -r etl_requirements.txt

# Check installation
pip list | grep xlrd
```

### Issue 5: PostgreSQL Version Too Old

Upgrade PostgreSQL:

**Windows:**
- Use PostgreSQL installer for newer version
- Or use PostgreSQL Stack Builder

**macOS:**
```bash
# Using Homebrew
brew upgrade postgresql@15

# Or reinstall
brew uninstall postgresql@15
brew install postgresql@15
```

**Linux:**
```bash
# Ubuntu
sudo apt update && sudo apt upgrade postgresql

# CentOS
sudo yum upgrade postgresql15
```

---

## Verification & Testing

### Test 1: PostgreSQL Connection

```bash
# Connect using configured credentials
psql -h localhost -U rj_etl_user -d rj_hotel

# In psql prompt:
SELECT version();
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'rj_data';
\q
```

### Test 2: Python Environment

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "xlrd|psycopg2|numpy"

# Test imports
python -c "
import xlrd
import psycopg2
import numpy
print('All modules loaded successfully')
"
```

### Test 3: ETL Script

```bash
# Run with help
python rj_etl_pipeline.py --help

# Should show usage information
```

### Test 4: Single File Processing

```bash
# Create test file or use existing
python rj_etl_pipeline.py --mode single --file "test_rj_file.xls"

# Should complete without errors
```

### Test 5: Data Validation

```bash
python validate_data.py --config db_config.json

# Should show validation report
```

### Test 6: Full System Test

Create `test_system.sh` (macOS/Linux) or `test_system.bat` (Windows):

**Bash:**
```bash
#!/bin/bash

echo "Testing RJ ETL Pipeline Installation"
echo "======================================"

echo -n "PostgreSQL: "
psql --version || echo "FAIL"

echo -n "Python: "
python3 --version || echo "FAIL"

echo -n "xlrd: "
python3 -c "import xlrd; print('OK')" || echo "FAIL"

echo -n "psycopg2: "
python3 -c "import psycopg2; print('OK')" || echo "FAIL"

echo -n "Database connection: "
psql -U rj_etl_user -d rj_hotel -c "SELECT 1" &>/dev/null && echo "OK" || echo "FAIL"

echo -n "Schema exists: "
psql -U rj_etl_user -d rj_hotel -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='rj_data'" &>/dev/null && echo "OK" || echo "FAIL"

echo "======================================"
echo "Installation testing complete"
```

**Batch (Windows):**
```batch
@echo off
echo Testing RJ ETL Pipeline Installation
echo ======================================

echo.
echo Python:
python --version

echo.
echo PostgreSQL:
psql --version

echo.
echo Testing xlrd:
python -c "import xlrd; print('xlrd: OK')"

echo.
echo Testing psycopg2:
python -c "import psycopg2; print('psycopg2: OK')"

echo.
echo Testing database connection:
psql -U rj_etl_user -d rj_hotel -c "SELECT 1"

echo.
echo ======================================
echo Installation testing complete
pause
```

---

## Docker Installation (Optional)

Complete Docker setup:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY etl_requirements.txt .
RUN pip install --no-cache-dir -r etl_requirements.txt

COPY . .

RUN chmod +x *.py *.sh

ENTRYPOINT ["python", "rj_etl_pipeline.py"]
```

Build and run:
```bash
# Build image
docker build -t rj_etl:latest .

# Run single file
docker run -v /data:/data rj_etl \
  --mode single --file "/data/Rj_01-15-2024.xls"

# Run batch with custom config
docker run -v /data:/data -v /config:/config rj_etl \
  --mode batch --folder /data --config /config/db_config.json
```

---

## Post-Installation Configuration

### Create Dedicated Database User (Optional)

For production, create a limited-privilege user:

```sql
-- Connect as superuser
psql -U postgres -d rj_hotel

-- Create ETL user with limited privileges
CREATE ROLE rj_etl_readonly LOGIN PASSWORD 'read_password';
GRANT CONNECT ON DATABASE rj_hotel TO rj_etl_readonly;
GRANT USAGE ON SCHEMA rj_data TO rj_etl_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA rj_data TO rj_etl_readonly;

-- Create ETL user with write privileges
CREATE ROLE rj_etl_write LOGIN PASSWORD 'write_password';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA rj_data TO rj_etl_write;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA rj_data TO rj_etl_write;
```

### Configure PostgreSQL for Performance

Edit `postgresql.conf` (location varies by OS):

```ini
# Connection settings
max_connections = 200

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# WAL settings
wal_buffers = 16MB
default_statistics_target = 100

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Enable Connection Logging

```sql
-- Connect as superuser
psql -U postgres -c "
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_statement = 'all';
"

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Next Steps

1. **Review Documentation**: Read README.md and QUICKSTART.md
2. **Test with Sample Data**: Process a few test files first
3. **Schedule Automation**: Set up cron jobs or Task Scheduler
4. **Monitor Performance**: Use validate_data.py regularly
5. **Backup Strategy**: Implement regular database backups

---

Congratulations! Your RJ ETL Pipeline is now installed and ready to use.

For next steps, see: **QUICKSTART.md** or **README.md**
