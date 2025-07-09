# Dual Credit Course Updater

A Python application for updating dual credit course information in the Aeries Student Information System. This tool automatically updates student history records with appropriate credit hours for dual credit courses, with intelligent handling of year-long courses and different grading requirements.

## Features

- Queries dual credit courses from Aeries database
- Processes students individually with year-by-year course analysis
- Intelligent handling of year-long courses with special grading rules:
  - **Course 8250 variants**: Requires C or better in at least one semester
  - **Course 3160**: Requires passing only the second semester (TE = 2)
  - **Regular year-long courses**: Requires passing both semesters
- Updates student history records with credit hours for passed courses
- Updates SDE/ST designations for all dual credit courses (passed and failed)
- Supports both production and testing environments
- Comprehensive logging with function timing and detailed course processing
- Course-specific credit hour mapping with 40+ supported courses
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
   DEFAULT_SCHOOL_ST=Default school ST for HIS records
   DEFAULT_SCHOOL_SDE=Default school SDE for HIS records
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

## Processing Logic

### Student-by-Student Processing

The application now processes each student individually, analyzing their courses year by year to properly handle:

1. **Year-Long Course Detection**: Identifies courses with both semester 1 and 2 records
2. **Special Grading Rules**: Applies course-specific passing requirements
3. **Credit Hour Assignment**: Awards credit hours only to students who meet passing criteria
4. **SDE/ST Updates**: Updates special designations for all dual credit courses regardless of pass/fail status

### Year-Long Course Handling

- **Course 8250 variants (8250, 8250CE, 8250SD)**: Student needs C or better in at least one semester
- **Course 3160**: Student needs to pass only the second semester (TE = 2)
- **All other year-long courses**: Student must pass both semesters

### Grade Processing

The application recognizes passing grades as:

- A grades (A+, A, A-)
- B grades (B+, B, B-)
- C grades (C+, C, C-)
- P (Pass)

## Database Schema

The application works with the following key database fields:

- `PID`: Student ID
- `CN`: Course Number
- `SQ`: Sequence Number (semester: 1 or 2)
- `TE`: Term (1 or 2)
- `MK`: Grade/Mark
- `YR`: Academic Year
- `CH`: Credit Hours
- `SDE`: Special Designation (defaults to 16 → `SLHS`)
- `ST`: Status (defaults to 20 → `Chabot Comm College`)

## SQL Queries

### Dual Credit Course Selection

The application selects courses based on:

- Active records (del = 0)
- Active students (stu.del = 0, stu.tg = '')
- Grades 9-12 (gr in 9,10,11,12)
- Specific course numbers from the dual credit list (65+ courses)

### Record Updates

Two types of updates are performed:

1. **Passed Courses**: Updates CH (credit hours), SDE, and ST
2. **Failed Courses**: Updates only SDE and ST (no credit hours awarded)

## Logging

The application provides detailed logging through the `slusdlib.core` module:

- Function execution timing via `@decorators.log_function_timer`
- Student-by-student processing progress
- Year-by-year course analysis
- Course passing/failing status with reasoning
- Database operation results
- Error handling and rollback notifications
- Skipped courses not in mapping dictionary

## Error Handling

- Database connection failures are logged and handled
- Missing course mappings are logged and skipped
- Transaction rollbacks occur on update failures
- Individual record failures don't stop the entire process
- Graceful handling of missing grade data

## File Structure

```text
├── main.py                          # Main application file (updated logic)
├── main_old.py                      # Previous version (row-by-row processing)
├── course_hour_mappings.py          # Course number to credit hours mapping
├── SQL/
│   ├── dual_credit_courses.sql      # Query for dual credit courses
│   ├── update_his_dual_credit_pass.sql  # Update query for passed courses
│   └── update_his_dual_credit_fail.sql  # Update query for failed courses
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Functions

### `update_his_record(pid, cn, sq, credit_hours, sde=16, st=20)`

Updates a single HIS record with credit hours for passed courses.

### `update_his_record_sde_st_only(pid, cn, sq, sde=16, st=20)`

Updates a single HIS record with only SDE and ST for failed courses (no credit hours).

### `is_passing_grade(grade)`

Determines if a grade is passing (A, B, C, or P).

### `check_year_long_pass(courses)`

Analyzes courses for a student in a specific year to determine pass/fail status with special handling for year-long courses.

### `update_dual_credit_hist()`

Main function that processes all dual credit courses student-by-student, year-by-year.

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
- The previous row-by-row processing logic is preserved in `main_old.py` for reference
