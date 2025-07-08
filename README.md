# Dual Credit Course Updater

A Python application for updating dual credit course information in the Aeries Student Information System. This tool automatically updates student history records with appropriate credit hours for dual credit courses.

## Features

- Queries dual credit courses from Aeries database
- Updates student history records with credit hours
- Supports both production and testing environments
- Comprehensive logging with function timing
- Course-specific credit hour mapping

## Prerequisites

- Python 3.x
- Required Python packages:
  - pandas
  - sqlalchemy
  - python-decouple
  - slusdlib (custom library)

## Installation

1. Clone the repository
2. Install required dependencies:

   ```bash
   pip install pandas sqlalchemy python-decouple
   ```

3. Set up your environment variables by copying `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

4. Configure your environment variables in `.env`:

   ```env
   TEST=False  # Set to True for testing, False for production
   DATABASE=your_production_database_name
   TEST_DATABASE=your_test_database_name
   ```

## Usage

### Basic Usage

Run the main script to update all dual credit course records:

```bash
python main.py
```

### Find Specific Course Data

Uncomment the `find_course()` call in the main block to export data for a specific course:

```python
find_course('CCC289')  # Exports course data to CCC289.csv
```

## Configuration

### Environment Variables

- `TEST`: Boolean flag for testing mode
- `DATABASE`: Production database name
- `TEST_DATABASE`: Test database name (defaults to 'DST24000SLUSD_DAILY')

### Course Credit Hours

The application includes a mapping dictionary for course numbers to credit hours. Currently supported courses include:

- **3 Credit Hour Courses**: 4141, 4142, 5343, 5361, 6608AC, 6614AC, 6615AC, and many others
- **2.5 Credit Hour Courses**: 76241, 76251, L5795
- **2 Credit Hour Courses**: 75551, 75552, 8250, 8250CE, 8250SD, L8000
- **1.5 Credit Hour Courses**: 75554, L7540
- **4 Credit Hour Courses**: 3160

## Database Schema

The application works with the following key database fields:

- `PID`: Student ID
- `CN`: Course Number
- `SQ`: Sequence Number
- `CH`: Credit Hours
- `SDE`: Special Designation (defaults to 16)
- `ST`: Status (defaults to 20)

## SQL Queries

### Dual Credit Course Selection

The application selects courses based on:

- Active records (del = 0)
- Grades 9-12 (gr in 9,10,11,12)
- Passing marks (A%, B%, C%, P)
- Specific course numbers from the dual credit list

### Record Updates

Updates are performed using parameterized queries to prevent SQL injection.

## Logging

The application uses comprehensive logging through the `slusdlib.core` module:

- Function execution timing
- Database operation results
- Error handling and rollback notifications

## Error Handling

- Database connection failures are logged and handled
- Missing course mappings are logged and skipped
- Transaction rollbacks occur on update failures

## File Structure

```text
├── main.py                          # Main application file
├── SQL/
│   ├── dual_credit_courses.sql      # Query for dual credit courses
│   └── update_his_dual_credit.sql   # Update query for HIS records
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Security Notes

- Database credentials are managed through environment variables
- SQL queries use parameterized statements to prevent injection
- Write access to the database is required for updates
