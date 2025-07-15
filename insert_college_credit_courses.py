import math
from pandas import read_csv, read_sql_query
from slusdlib import aeries, core, decorators
from sqlalchemy import text
from decouple import config
from icecream import ic
from course_hour_mappings import COURSE_HOURS_MAPPING

SQL = core.build_sql_object()
CNXN = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str), access_level='w')
DEFAULT_SCHOOL_ST = config('DEFAULT_SCHOOL_ST', cast=int) 
DEFAULT_SCHOOL_SDE = config('DEFAULT_SCHOOL_SDE', cast=int) 
ROP_LOCATION_CODE_ST = config('ROP_LOCATION_CODE_ST', cast=int)
PASSING_MARKS = ['A', 'B', 'C', 'P']
COURSE_MAP = read_csv('in_data/chabot_course_map.csv')\
    .set_index('CRN')[['SLUSD Course Code', 'Coll Units']]\
    .to_dict('index')
    # .apply(lambda x: {'SLUSD_course_code': x[0], 'Coll Units': x[1]}, axis=1)\

def get_distilled_mark(mark: str) -> str:
    if mark in PASSING_MARKS:
        return mark
    elif 'NGR' in mark:
        return 'NGR'
    else:
        raise ValueError(f"Unexpected grade value: {mark}")
    
def get_next_sq(pid: int = None, id: int = None, table: str = 'his') -> int:
    if pid:
        sql = text(f"""
                select 
                top 1 
                sq
                from {table} 
                where pid = :pid
                order by sq desc
                """)
        last_sq = read_sql_query(sql, CNXN, params={'pid': pid})['sq'].iloc[0]
        return int(last_sq + 1) if last_sq is not None else 1
    elif id:
        sql = text(f"""
                select 
                top 1 
                sq
                from {table} 
                where id = :id
                order by sq desc
                """)
        last_sq = read_sql_query(sql, CNXN, params={'id': id})['sq'].iloc[0]
        return int(last_sq + 1) if last_sq is not None else 1

def insert_new_his_record(pid: int, cn: str, mk: str, cr: str, gr: str, te: str, yr: str, st: int, cc: str, sq: int, sde: int, ch: float) -> None:
    with CNXN.connect() as conn:
        sql = text(SQL.insert_his_record)
        try:
            conn.execute(sql, {
                "pid":int(pid),
                "cn":cn,
                "mk":mk,
                "cr":cr,
                "gr":gr,
                "te":te,
                "yr":yr,
                "st":st,
                "cc":cc,
                "sq":sq,
                "sde":sde,
                "ch":ch
            })
            conn.commit()
            print(f"Successfully inserted new record for PID: {pid}, CN: {cn}, SQ: {sq}")
        
        except Exception as e:
            print(f"Error retrieving SQL template: {e}")
    return

           
def insert_college_credit_courses(courses_file_path: str = 'in_data/chabot_courses_taken.csv',  school_taken:int = DEFAULT_SCHOOL_ST, school_dual_enrollment:int = DEFAULT_SCHOOL_SDE) -> None:
    all_courses = read_csv(courses_file_path)
    yr = config('DATABASE', cast=str)[3:5]
    passed_courses = all_courses[all_courses['Grade (NGR = No Grade Received)'].isin(PASSING_MARKS)]
    for index, row in passed_courses.iterrows():
        slusd_id = row.get('ID', None)
        college_course_number = row['CRN']
        

        slusd_course_code = COURSE_MAP[college_course_number]['SLUSD Course Code'] if college_course_number in COURSE_MAP else None
        
        if slusd_course_code is None or (type(slusd_course_code) == float and math.isnan(slusd_course_code)):
            slusd_course_code = '60001C'
        ic(slusd_course_code)
        
        course_info = read_sql_query(text(SQL.course_info), CNXN, params={'cn': slusd_course_code})
        mark = get_distilled_mark(row['Grade (NGR = No Grade Received)']) 
        grade = row['GR']
        # if slusd_id is None or math.isnan(slusd_course_code):
        #     print(f"Skipping row {index} because 'ID' or 'SLUSD Course Code' is missing.")
        #     continue
        # if mark not in PASSING_MARKS:
        #     if mark == 'NGR':
        #         print(f"Skipping row {index} because 'Grade' is NGR (No Grade Received).")
        #         continue
        #     print(f"Skipping row {index} because 'Grade' is not valid: {mark}")
        #     continue
        
        # print(COURSE_MAP)
        ic(COURSE_MAP[college_course_number])
        
        print(COURSE_MAP[college_course_number])
        credits_possible = course_info['CR'].iloc[0] if not course_info.empty else 5.00
        term = course_info['TM'].iloc[0] if not course_info.empty else 1
        credits_complete = credits_possible if mark in PASSING_MARKS else 0.00
        next_sq = get_next_sq(slusd_id)
        ch = COURSE_MAP[college_course_number]['Coll Units'] if slusd_course_code in COURSE_MAP else 0.00
        
        print(f"Inserting course for SLUSD ID: {slusd_id}, Course Code: {slusd_course_code}, Grade: {mark}, Credits Possible: {credits_possible}, Credits Complete: {credits_complete}, Next SQ: {next_sq}")
        
        print(f"Course info for {slusd_course_code}: CR = {credits_possible}, ch = {ch}")
        
        
        print(f"Processing row {index}: SLUSD ID: {slusd_id}, College Course Number: {college_course_number}, SLUSD Course Code: {slusd_course_code}, Grade: {mark}")
        # print(f"Inserting course for SLUSD ID: {slusd_id}, Course Code: {slusd_course_code}, Grade: {mark}")
        insert_new_his_record(
            pid=slusd_id,
            cn=slusd_course_code,
            mk=mark,
            cr=credits_possible,
            gr=grade,
            te=term,
            yr=yr,
            st=school_taken,
            cc=float(credits_complete),
             sq=next_sq,
             sde=school_dual_enrollment,
             ch=ch
            )
        break
    

if __name__ == "__main__":
    insert_college_credit_courses()