# Dual Credit Course Updater

A Python application for updating dual credit course information in the Aeries Student Information System. This tool automatically updates student history records with appropriate credit hours for dual credit courses.

## Features

- Queries dual credit courses from Aeries database
- Updates student history records with credit hours and special designations
- Supports both production and testing environments
- Comprehensive logging with function timing
- Course-specific credit hour mapping with 65+ supported courses
- Exports course data for analysis

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

The application includes a comprehensive mapping dictionary for course numbers to credit hours in `course_hour_mappings.py`. Currently supported courses include:

- **4 Credit Hour Courses**: 3160
- **3 Credit Hour Courses**: 4141, 4142, 5343, 5361, 6608AC, 6614AC, 6615AC, 75701, 75702, 75712, 75801, 75811, 75941, 75951, 76011, 76012, 76051, 76052, 76141, 76151, 79102, 79201, 79211, 79212, 79220, 79221, 79230, 79231, L65051, L7535, L7573, L7581, L7594, L7601, L7614
- **2.5 Credit Hour Courses**: 76241, 76251, L5795
- **2 Credit Hour Courses**: 75551, 75552, 8250, 8250CE, 8250SD, L8000
- **1.5 Credit Hour Courses**: 75554, L7540

## Database Schema

The application works with the following key database fields:

- `PID`: Student ID
- `CN`: Course Number
- `SQ`: Sequence Number
- `CH`: Credit Hours
- `SDE`: Special Designation (defaults to 16 --> `SLHS`)
- `ST`: Status (defaults to 20 --> `Chabot Comm College`)

## SQL Queries

### Dual Credit Course Selection

The application selects courses based on:

- Active records (del = 0)
- Grades 9-12 (gr in 9,10,11,12)
- Passing marks (A%, B%, C%, P)
- Specific course numbers from the dual credit list (65+ courses)

### Record Updates

Updates are performed using parameterized queries to prevent SQL injection and update the HIS table with:

- Credit hours based on course mapping
- Special designation (SDE = 16)
- Status (ST = 20)

## Logging

The application uses comprehensive logging through the `slusdlib.core` module:

- Function execution timing via `@decorators.log_function_timer`
- Database operation results
- Error handling and rollback notifications
- Skipped courses not in mapping dictionary

## Error Handling

- Database connection failures are logged and handled
- Missing course mappings are logged and skipped
- Transaction rollbacks occur on update failures
- Individual record failures don't stop the entire process

## File Structure

```text
├── main.py                          # Main application file
├── course_hour_mappings.py          # Course number to credit hours mapping
├── SQL/
│   ├── dual_credit_courses.sql      # Query for dual credit courses
│   └── update_his_dual_credit.sql   # Update query for HIS records
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Functions

### `update_his_record(pid, cn, sq, credit_hours, sde=16, st=20)`

Updates a single HIS record with the specified parameters.

### `update_dual_credit_hist()`

Main function that processes all dual credit courses and updates their records.

### `find_course(course)`

Utility function to export data for a specific course to CSV for analysis.

### `get_course_hours(course_number)`

Returns credit hours for a given course number, or None if not found.

## Security Notes

- Database credentials are managed through environment variables
- SQL queries use parameterized statements to prevent injection
- Write access to the database is required for updates
- Environment-specific database connections based on TEST flag

## Development Notes

- The application supports both production and test database environments
- CSV exports and logs are ignored in version control
- The `slusdlib` custom library handles database connections and logging
- Course mappings can be easily extended by adding to the dictionary in `course_hour_mappings.py`
