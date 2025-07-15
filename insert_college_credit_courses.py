import math
from pandas import read_csv, read_sql_query
from slusdlib import aeries, core, decorators
from sqlalchemy import text
from decouple import config
from icecream import ic
from course_hour_mappings import COURSE_HOURS_MAPPING

SQL = core.build_sql_object()
CNXN = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str), access_level='w')
DEFAULT_SCHOOL_ST = 20 #config('DEFAULT_SCHOOL_ST', cast=int) 
DEFAULT_SCHOOL_SDE = config('DEFAULT_SCHOOL_SDE', cast=int) 
ROP_LOCATION_CODE_ST = config('ROP_LOCATION_CODE_ST', cast=int)
PASSING_MARKS = ['A', 'B', 'C', 'P']
COURSE_MAP = read_csv('in_data/chabot_course_map.csv')\
    .set_index('CRN')[['SLUSD Course Code', 'Coll Units','Course Title (Long Title)']]\
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

def insert_new_his_record(pid: int, cn: str, mk: str, cr: float, gr: int,  yr: int, st: int, cc: float, sq: int, sde: int, ch: float, sid:int = 9999999999, co:str = '', te: int = 1) -> None:
    params = {
        "pid": int(pid),
        "cn": str(cn),
        "co": str(co), 
        "mk": str(mk),
        "cr": float(cr),
        "gr": int(gr),
        "te": int(te), 
        "yr": int(yr),
        "st": int(st),
        "cc": float(cc),
        "sq": int(sq),
        "sid": int(sid),
        "sde": int(sde),
        "ch": float(ch)
    }
    
    # Debug logging
    # print(f"DEBUG - Parameters being passed:")
    # for key, value in params.items():
    #     print(f"  {key}: {value} (type: {type(value)})")
    
    with CNXN.connect() as conn:
        sql = text(SQL.insert_his_record)
        try:
            conn.execute(sql, params)
            conn.commit()
            core.log(f"Successfully inserted new record for PID: {pid}, CN: {cn}, SQ: {sq}")
        except Exception as e:
            core.log(f"Error inserting record: {e}")
            raise
@decorators.log_function_timer
def insert_college_credit_courses(courses_file_path: str = 'in_data/chabot_courses_taken.csv',  school_taken:int = DEFAULT_SCHOOL_ST, school_dual_enrollment:int = DEFAULT_SCHOOL_SDE) -> None:
    all_courses = read_csv(courses_file_path)
    yr = config('DATABASE', cast=str)[3:5]
    passed_courses = all_courses[all_courses['Grade (NGR = No Grade Received)'].isin(PASSING_MARKS)]
    for index, row in passed_courses.iterrows():
        
        slusd_id = row.get('ID', None)
        core.log(f" Processing row {index} with Student ID: {slusd_id} ".center(80, '#'))
        if slusd_id is None or slusd_id == '' or math.isnan(slusd_id) or slusd_id == 'nan':
            core.log(f"Skipping row {index} because 'ID' is missing.")
            continue
        college_course_number = row['CRN']
        

        slusd_course_code = COURSE_MAP[college_course_number]['SLUSD Course Code'] if college_course_number in COURSE_MAP else None
        
        # if slusd_course_code is None or (type(slusd_course_code) == float and math.isnan(slusd_course_code)):
        #     slusd_course_code = '60001C'
        
        course_info = read_sql_query(text(SQL.course_info), CNXN, params={'cn': slusd_course_code})
        mark = get_distilled_mark(row['Grade (NGR = No Grade Received)']) 
        grade = int(float(row['GR']))
        # if slusd_id is None or (type(slusd_course_code) == float and math.isnan(slusd_course_code)):
        #     core.log(f"Skipping row {index} because 'ID' or 'SLUSD Course Code' is missing.")
        #     continue
        if mark not in PASSING_MARKS:
            if mark == 'NGR':
                core.log(f"Skipping row {index} because 'Grade' is NGR (No Grade Received).")
                continue
            core.log(f"Skipping row {index} because 'Grade' is not valid: {mark}")
            continue
        
        credits_possible = course_info['CR'].iloc[0] if not course_info.empty else 5.00
        term = course_info['TM'].iloc[0] if not course_info.empty else 1
        credits_complete = credits_possible if mark in PASSING_MARKS else 0.00
        next_sq = get_next_sq(slusd_id)
        ch = COURSE_MAP[college_course_number]['Coll Units'] # if slusd_course_code in COURSE_MAP else 0.00
        co = COURSE_MAP[college_course_number]['Course Title (Long Title)'][:30] if COURSE_MAP[college_course_number]['Course Title (Long Title)'] else ''
        print(f'co: {co}')
        
        core.log(f"Inserting course for SLUSD ID: {slusd_id}, Course Code: {slusd_course_code}, Grade: {mark}, Credits Possible: {credits_possible}, Credits Complete: {credits_complete}, Next SQ: {next_sq}")
        
        core.log(f"Course info for {slusd_course_code}: CR = {credits_possible}, ch = {ch}")
        
        
        core.log(f"Processing row {index}: SLUSD ID: {slusd_id}, College Course Number: {college_course_number}, SLUSD Course Code: {slusd_course_code}, Grade: {mark}")
        insert_new_his_record(
            pid=int(slusd_id),
            cn=str(slusd_course_code),
            mk=str(mark),
            cr=float(credits_possible),
            co=str(co),  
            gr=int(grade),               
            # te=int(term),               
            yr=int(yr),                 
            st=int(school_taken),       
            cc=float(credits_complete), 
            sq=int(next_sq),           
            sde=int(school_dual_enrollment), 
            ch=float(ch)             
        )
        
        
    

if __name__ == "__main__":
    core.log("$"*80)
    core.log(f"Starting insert_college_credit_courses")
    insert_college_credit_courses()
    core.log("$"*80)
    