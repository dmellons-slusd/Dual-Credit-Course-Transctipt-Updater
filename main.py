from pandas import read_sql_query
from slusdlib import aeries, core, decorators
from course_hour_mappings import COURSE_HOURS_MAPPING, get_course_hours
from sqlalchemy import text
from decouple import config

sql = core.build_sql_object()
cnxn = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str, default='DST24000SLUSD_DAILY'), access_level='w')

def update_his_record(pid: int, cn: str, sq: str, credit_hours: float, sde: int = 16, st: int = 20) -> None:
    """Update a single HIS record with dual credit information including credit hours."""
    core.log(f"Updating HIS record (with credit hours) for PID: {pid}, CN: {cn}, SQ: {sq}")
    try:
        with cnxn.connect() as conn:
            conn.execute(
                text(sql.update_his_dual_credit_pass),
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
        cnxn.rollback()
        raise

def update_his_record_sde_st_only(pid: int, cn: str, sq: str, sde: int = 16, st: int = 20) -> None:
    """Update a single HIS record with only SDE and ST (for failed courses)."""
    core.log(f"Updating HIS record (SDE/ST only) for PID: {pid}, CN: {cn}, SQ: {sq}")
    try:
        with cnxn.connect() as conn:
            conn.execute(
                text(sql.update_his_dual_credit_fail),
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
        cnxn.rollback()
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

def check_year_long_pass(courses) -> dict:
    """
    Check if a student has passed both semesters of year-long courses.
    Special handling:
    - Course 8250 variants: only need C or better in one semester
    - Course 3160: only need to pass the second semester (TE == 2)
    
    Args:
        courses: DataFrame of courses for a student in a specific year
        
    Returns:
        dict: Dictionary mapping course numbers to pass status
              {course_number: {'passed': bool, 'semesters': [semester_data]}}
    """
    course_status = {}
    
    # Group courses by course number (CN)
    course_groups = courses.groupby('CN')
    
    for cn, course_group in course_groups:
        # Check if this course has both semester 1 and 2
        semesters = course_group['SQ'].unique()
        
        if len(semesters) == 2 and set(semesters) == {'1', '2'}:
            # This is a year-long course
            semester_data = []
            
            for _, row in course_group.iterrows():
                grade = row.get('MK', '')  # Assuming 'MK' is the grade column
                passed = is_passing_grade(grade)
                semester_data.append({
                    'semester': row['SQ'],
                    'term': row.get('TE', ''),
                    'grade': grade,
                    'passed': passed
                })
            
            # Special handling for course 8250 variants
            if cn in ['8250', '8250CE', '8250SD']:
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
                
            # Special handling for course 3160
            elif cn == '3160':
                # For 3160, only need to pass the second semester (TE == 2)
                second_semester_passed = False
                for sem_data in semester_data:
                    if sem_data['term'] == '2' and sem_data['passed']:
                        second_semester_passed = True
                        break
                
                course_status[cn] = {
                    'passed': second_semester_passed,
                    'semesters': semester_data,
                    'is_year_long': True
                }
                
                core.log(f"Course 3160: {'PASSED' if second_semester_passed else 'FAILED'} - needs to pass second semester (TE=2)")
                
            else:
                # Regular year-long courses need both semesters passed
                all_passed = all(sem_data['passed'] for sem_data in semester_data)
                course_status[cn] = {
                    'passed': all_passed,
                    'semesters': semester_data,
                    'is_year_long': True
                }
                
                core.log(f"Year-long course {cn}: {'PASSED' if all_passed else 'FAILED'} both semesters")
            
        else:
            # Single semester course
            row = course_group.iloc[0]  
            grade = row.get('MK', '')
            passed = is_passing_grade(grade)
            
            course_status[cn] = {
                'passed': passed,
                'semesters': [{'semester': row['SQ'], 'term': row.get('TE', ''), 'grade': grade, 'passed': passed}],
                'is_year_long': False
            }
            
            core.log(f"Single semester course {cn}: {'PASSED' if passed else 'FAILED'}")
    
    return course_status

@decorators.log_function_timer
def update_dual_credit_hist() -> None:
    """Main function to update dual credit history records."""
    data = read_sql_query(sql.dual_credit_courses, cnxn)
    if data.empty: 
        core.log("No dual credit courses found to update.")
        return
      
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
            
            course_status = check_year_long_pass(courses)
            
            # Update records for all courses (passed courses get credit hours, failed courses get SDE/ST only)
            for index, row in courses.iterrows():
                core.log(f" Processing course CN: {row['CN']} ".center(55, '-').center(80, ' '))
                cn = str(row['CN'])  
                sq = str(row['SQ'])  
                pid_int = int(row['PID'])  
                credit_hours = get_course_hours(cn)
                
                if credit_hours is None:
                    core.log(f"Course CN {cn} not found in translation dictionary. Skipping for PID {pid_int}.")
                    continue
                
                # Check if this course was passed
                if cn in course_status:
                    if course_status[cn]['passed']:
                        core.log(f"Course {cn} passed - updating record with credit hours")
                        update_his_record(pid_int, cn, sq, credit_hours)
                    else:
                        core.log(f"Course {cn} not passed - updating SDE/ST only for PID {pid_int}")
                        update_his_record_sde_st_only(pid_int, cn, sq)
                else:
                    core.log(f"Course {cn} status unknown - updating SDE/ST only for PID {pid_int}")
                    update_his_record_sde_st_only(pid_int, cn, sq)

def find_course(course: str) -> None:
    """Export data for a specific course to CSV for analysis."""
    data = read_sql_query(sql.dual_credit_courses, cnxn)
    course_data = data[data['CN'] == course]
    course_data.to_csv(f'{course}.csv', index=False)
    core.log(f"Exported {len(course_data)} records for course {course} to {course}.csv")

if __name__ == "__main__":
    core.log("$"*80)
    core.log(f"Starting update_dual_credit_hist")
    update_dual_credit_hist()
    # find_course('CCC289')
    core.log("~"*80)