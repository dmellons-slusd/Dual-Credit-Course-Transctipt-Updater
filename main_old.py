from pandas import read_sql_query
from slusdlib import aeries, core, decorators
from course_hour_mappings import COURSE_HOURS_MAPPING, get_course_hours
from sqlalchemy import text
from decouple import config

sql = core.build_sql_object()
cnxn = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str), access_level='w')
def update_his_record(pid: int, cn: str, sq: str, credit_hours: int, sde: int = 16, st: int = 20) -> None:

    core.log(f"Updating HIS record for PID: {pid}, CN: {cn}, SQ: {sq}")
    try:
        with cnxn.connect() as conn:
            conn.execute(
                text(sql.update_his_dual_credit),
                                                  
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
            core.log(f"Successfully updated record")
    except Exception as e:
        core.log(f"Error updating record for PID {pid}: {e}")
        cnxn.rollback()
        raise

@decorators.log_function_timer
def update_dual_credit_hist() -> None:
    data = read_sql_query(sql.dual_credit_courses, cnxn)
    if data.empty: 
        core.log("No dual credit courses found to update.")
        return
    for index, row in data.iterrows():
        pid = row['PID']
        cn = row['CN']
        sq = row['SQ']
        credit_hours = get_course_hours(cn)
        if credit_hours is None:
            core.log(f"Course CN {cn} not found in translation dictionary. Skipping for ID#{pid}.")
            continue
        update_his_record(pid, cn, sq, credit_hours)
        
def find_course(course: str) -> None:
    data = read_sql_query(sql.dual_credit_courses, cnxn)
    course_data = data[data['CN'] == course]
    course_data.to_csv(f'{course}.csv', index=False)
    
if __name__ == "__main__":
    core.log("~"*80)
    core.log(f"Starting update_dual_credit_hist")
    update_dual_credit_hist()
    # find_course('CCC289')
    core.log("~"*80)