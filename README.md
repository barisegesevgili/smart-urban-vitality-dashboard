# Flask Application with PostgreSQL

This is a Flask web application that uses PostgreSQL as its database.

## Setup Instructions

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Create and activate virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
- Install PostgreSQL if not already installed
- Create a new database
- Update the database connection details in `.env` file

5. Set up environment variables:
Create a `.env` file in the root directory and add:
```
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
FLASK_APP=app.py
FLASK_ENV=development
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
.
├── app.py              # Main application file
├── templates/          # HTML templates
├── requirements.txt    # Project dependencies
├── .env               # Environment variables (not in git)
└── README.md          # This file
```

## Development

- Make sure to activate the virtual environment before working on the project
- Install any new dependencies with `pip install <package>` and update requirements.txt:
  ```bash
  pip freeze > requirements.txt
  ```

## Deployment

The application includes Gunicorn for production deployment. 