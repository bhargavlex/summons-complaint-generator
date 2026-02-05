# Database Setup Guide

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Database

Make sure MySQL is running (via Docker or locally):

```bash
# If using Docker:
docker-compose up -d mysql

# Wait for MySQL to be ready, then:
```

### 4. Configure Database Connection

Create `.env` file in `backend/` directory:

```env
DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3306/appdb
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redispass
REDIS_DB=0
DEBUG=True
```

### 5. Initialize Database

```bash
# Make sure you're in backend/ directory with venv activated
python -m app.db.init_db
```

This will:
- ✅ Create all 7 tables
- ✅ Seed 2 law firms (COHAN LAW, Smith & Associates)
- ✅ Seed 3 case types (Premises, PI, Med Mal)
- ✅ Create 1 template (Premises for COHAN LAW)
- ✅ Create 20 template fields (all placeholders)

### 6. Upload Template File

After initialization, upload your template DOCX file to:
```
backend/templates/cohan/premises/summons_complaint.docx
```

Create the directory if it doesn't exist:
```bash
mkdir -p templates/cohan/premises
# Then copy your template file there
```

## Database Schema

### Tables Created:
1. `law_firms` - Law firm information
2. `case_types` - Case type categories
3. `templates` - Template files per firm+case_type
4. `template_fields` - All placeholders/fields
5. `sessions` - Processing sessions (one per job)
6. `documents` - Uploaded documents
7. `field_values` - Extracted and manual values

### Seed Data:
- **Law Firms**: COHAN LAW, PLLC | Smith & Associates
- **Case Types**: Premises Liability | Personal Injury | Medical Malpractice
- **Template**: Premises Liability for COHAN LAW (20 fields)

## Verify Setup

```bash
# Connect to MySQL and check tables
mysql -u appuser -papppass appdb -e "SHOW TABLES;"

# Check seed data
mysql -u appuser -papppass appdb -e "SELECT * FROM law_firms;"
mysql -u appuser -papppass appdb -e "SELECT * FROM template_fields WHERE template_id=1;"
```

## Troubleshooting

### Error: "Can't connect to MySQL"
- Make sure MySQL is running: `docker-compose ps`
- Check connection string in `.env`

### Error: "Table already exists"
- Database was already initialized
- To reset: Drop database and run init again

### Error: "Template file not found"
- Create directory: `mkdir -p templates/cohan/premises`
- Upload your template DOCX file there

## Next Steps

After database is set up:
1. ✅ Database schema ready
2. ⏳ Upload template DOCX file
3. ⏳ Test document upload
4. ⏳ Test LLM extraction
5. ⏳ Test preview generation
