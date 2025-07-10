from pandas import DataFrame, read_sql_query
from slusdlib import aeries, core, decorators
from course_hour_mappings import COURSE_HOURS_MAPPING, get_course_hours
from update_articulated_courses import update_articulated_courses
from sqlalchemy import text
from decouple import config

SQL = core.build_sql_object()
CNXN = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str), access_level='w')
DEFAULT_SCHOOL_ST = config('DEFAULT_SCHOOL_ST', cast=int) 
DEFAULT_SCHOOL_SDE = config('DEFAULT_SCHOOL_SDE', cast=int) 
ROP_LOCATION_CODE_ST = config('ROP_LOCATION_CODE_ST', cast=int)

def update_his_record(pid: int, cn: str, sq: str, credit_hours: float, sde: int = 16, st: int = DEFAULT_SCHOOL_ST) -> None:
    """Update a single HIS record with dual credit information including credit hours."""
    core.log(f"Updating HIS record (with credit hours) for PID: {pid}, CN: {cn}, SQ: {sq}")
    try:
        with CNXN.connect() as conn:
            conn.execute(
                text(SQL.update_his_dual_credit_pass),
                {
                    "sde": sde,
                    "st": st,
                    "pid": pid,
                    "cn": cn,
                    "sq": sq,
                    "credit_hours": credit_hours
                }
            )
            conn.commit()
            core.log(f"Successfully updated record with credit hours")
    except Exception as e:
        core.log(f"Error updating record for PID {pid}: {e}")
        CNXN.rollback()
        raise

def update_his_record_sde_st_only(pid: int, cn: str, sq: str, sde: int = 16, st: int = DEFAULT_SCHOOL_ST) -> None:
    """Update a single HIS record with only SDE and ST (for failed courses)."""
    core.log(f"Updating HIS record (SDE/ST only) for PID: {pid}, CN: {cn}, SQ: {sq}")
    try:
        with CNXN.connect() as conn:
            conn.execute(
                text(SQL.update_his_dual_credit_fail),
                {
                    "sde": sde,
                    "st": st,
                    "pid": pid,
                    "cn": cn,
                    "sq": sq
                }
            )
            conn.commit()
            core.log(f"Successfully updated record with SDE/ST only")
    except Exception as e:
        core.log(f"Error updating SDE/ST for PID {pid}: {e}")
        CNXN.rollback()
        raise

def is_passing_grade(grade: str) -> bool:
    """Check if a grade is passing (A, B, C, or P)."""
    if not grade:
        return False
    grade = str(grade).upper().strip()
    return (grade.startswith('A') or 
            grade.startswith('B') or 
            grade.startswith('C') or 
            grade == 'P')
  
    
def check_year_long_pass(courses: DataFrame, course_terms: dict) -> dict:
    """
    Check if a student has passed both semesters of year-long courses.
    Special handling:
    - Course 8250 variants: only need C or better in one semester
    - Regular year-long courses: pass if second semester is passed (even if first failed)
    
    Args:
        courses: DataFrame of courses for a student in a specific year
        course_terms: Dictionary mapping course numbers to term types
        
    Returns:
        dict: Dictionary mapping course numbers to pass status
              {course_number: {'passed': bool, 'semesters': [semester_data]}}
    """
    course_status = {}
    
    # Group courses by course number (CN)
    course_groups = courses.groupby('CN')
    
    for cn, course_group in course_groups:
        # Check if this course has both semester 1 and 2
        terms = course_group['TE'].unique()
        
        if (len(terms) == 2 and set(terms) == {1, 2}) or course_terms.get(cn, None) == 'Y':
            # This is a year-long course
            semester_data = []
            
            for _, row in course_group.iterrows():
                grade = row.get('MK', '')  
                passed = is_passing_grade(grade)
                semester_data.append({
                    'semester': row.get('TE', ''),  # TE is the term/semester
                    'term': row.get('TE', ''),
                    'grade': grade,
                    'passed': passed
                })
            
            # Special handling for course 8250 variants
            if cn in ['8250']:
                # For 8250 variants, only need C or better in one semester
                c_or_better_grades = []
                for sem_data in semester_data:
                    grade = sem_data['grade'].upper().strip() if sem_data['grade'] else ''
                    if grade.startswith('A') or grade.startswith('B') or grade.startswith('C'):
                        c_or_better_grades.append(sem_data)
                
                passed_8250 = len(c_or_better_grades) >= 1
                course_status[cn] = {
                    'passed': passed_8250,
                    'semesters': semester_data,
                    'is_year_long': True
                }
                
                core.log(f"8250 variant course {cn}: {'PASSED' if passed_8250 else 'FAILED'} - needs C or better in one semester")
                
            else:
                # Regular year-long courses: pass if second semester is passed
                # Find semester 1 and 2 data
                sem1_data = next((sem for sem in semester_data if sem['semester'] == 1), None)
                sem2_data = next((sem for sem in semester_data if sem['semester'] == 2), None)
                
                # Course passes if second semester is passed
                if sem2_data and sem2_data['passed']:
                    course_passed = True
                    if sem1_data and not sem1_data['passed']:
                        core.log(f"Year-long course {cn}: PASSED - failed first semester but passed second semester")
                    else:
                        core.log(f"Year-long course {cn}: PASSED - passed second semester")
                else:
                    course_passed = False
                    core.log(f"Year-long course {cn}: FAILED - did not pass second semester")
                
                course_status[cn] = {
                    'passed': course_passed,
                    'semesters': semester_data,
                    'is_year_long': True
                }
            
        else:
            # Single semester course
            row = course_group.iloc[0]  
            grade = row.get('MK', '')
            passed = is_passing_grade(grade)
            
            course_status[cn] = {
                'passed': passed,
                'semesters': [{'semester': row.get('TE', ''), 'term': row.get('TE', ''), 'grade': grade, 'passed': passed}],
                'is_year_long': False
            }
            
            core.log(f"Single semester course {cn}: {'PASSED' if passed else 'FAILED'}")
    
    return course_status

@decorators.log_function_timer
def update_dual_credit_hist() -> None:
    """Main function to update dual credit history records."""
    data = read_sql_query(SQL.dual_credit_courses, CNXN)
    if data.empty: 
        core.log("No dual credit courses found to update.")
        return
    course_terms = get_course_terms()  
    # Process each student individually
    student_ids = data['PID'].unique()
   
    for pid in student_ids:
        core.log(f" Processing student PID: {pid} ".center(80, '#'))
        student_data = data[data['PID'] == pid].sort_values(by=['YR', 'TE'], ascending=[False, True])
        years = student_data['YR'].unique()
        
        core.log(f"Student# {pid} with {len(years)} years of data")
        
        for year in years:
            core.log(f" Processing year: {year} ".center(70, '*').center(80, ' '))
            courses = student_data[student_data['YR'] == year]
            core.log(f"Processing PID: {pid}, Year: {year} with {len(courses)} courses")
            
            course_status = check_year_long_pass(courses, course_terms)
            
            # Update records for all courses (passed courses get credit hours, failed courses get SDE/ST only)
            for index, row in courses.iterrows():
                core.log(f" Processing course CN: {row['CN']} ".center(55, '-').center(80, ' '))
                cn = str(row['CN'])  
                sq = str(row['SQ'])  
                pid_int = int(row['PID'])  
                credit_hours = get_course_hours(cn)
                location_code_st = check_offered_at_location(cn)
                
                if credit_hours is None:
                    core.log(f"Course CN {cn} not found in translation dictionary. Skipping for PID {pid_int}.")
                    continue
                
                # Check if this course was passed
                if cn in course_status:
                    if course_status[cn]['passed']:
                        core.log(f"Course {cn} passed - updating record with credit hours")
                        if course_status[cn]['is_year_long']:
                            # For year-long courses, split credit hours between semesters
                            credit_hours = credit_hours / 2 if credit_hours else 0

                        update_his_record(pid_int, cn, sq, credit_hours, st=location_code_st)
                    else:
                        core.log(f"Course {cn} not passed - updating SDE/ST only for PID {pid_int}")
                        
                        update_his_record_sde_st_only(pid_int, cn, sq, st=location_code_st)
                else:
                    core.log(f"Course {cn} status unknown - updating SDE/ST only for PID {pid_int}")
                    update_his_record_sde_st_only(pid_int, cn, sq, st=location_code_st)

def find_course(course: str) -> None:
    """Export data for a specific course to CSV for analysis."""
    data = read_sql_query(SQL.dual_credit_courses, CNXN)
    course_data = data[data['CN'] == course]
    course_data.to_csv(f'{course}.csv', index=False)
    core.log(f"Exported {len(course_data)} records for course {course} to {course}.csv")

def get_course_terms() -> dict:
    courses = f"'{"', '".join(list(COURSE_HOURS_MAPPING.keys()))}'"
    course_terms = read_sql_query(f"""
    select distinct cn, tm
    from crs
    where cn in ({courses})
    """, CNXN)
    return course_terms.set_index('cn')['tm'].to_dict()

def check_offered_at_location(cn: str) -> int:
    
    try:
        with CNXN.connect() as conn:
            result = conn.execute(text(SQL.check_offered_at_location), {"cn": cn})
            row = result.fetchone()
            department_code = row[0] if row else None
            
            if department_code is None:
                core.log(f"No location code found for course {cn}. Defaulting to {DEFAULT_SCHOOL_ST}.")
                return DEFAULT_SCHOOL_ST
            if department_code == 'R':
                return ROP_LOCATION_CODE_ST
            else:
                return DEFAULT_SCHOOL_ST
    except Exception as e:
        core.log(f"Error checking offered at location for course {cn}: {e}")
        return None
   


if __name__ == "__main__":
    core.log("$"*80)
    core.log(f"Starting update_dual_credit_hist")
    update_dual_credit_hist()
    core.log("$"*80)
    core.log(f"Starting update_articulated_courses")
    update_articulated_courses()
    core.log("$"*80)
    # check = check_offered_at_location('75341')
    # print(check)