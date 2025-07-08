from pandas import read_sql_query
from slusdlib import aeries, core, decorators
from sqlalchemy import text
from decouple import config

sql = core.build_sql_object()
cnxn = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str, default='DST24000SLUSD_DAILY'), access_level='w')
course_hourse_translation_dict = {
    "3160":	    4,
    "4141":	    3,
    "4142":	    3,
    "5343":	    3,
    "5361":	    3,
    "6608AC":	3,
    "6614AC":	3,
    "6615AC":	3,
    "75551":	2,
    "75552":	2,
    "75554":	1.5,
    "75701":	3,
    "75702":	3,
    "75712":	3,
    "75801":	3,
    "75811":	3,
    "75941":	3,
    "75951":	3,
    "76011":	3,
    "76012":	3,
    "76051":	3,
    "76052":	3,
    "76141":	3,
    "76151":	3,
    "76241":	2.5,
    "76251":	2.5,
    "79102":	3,
    "79201":	3,
    "79211":	3,
    "79212":	3,
    "79220":	3,
    "79221":	3,
    "79230":	3,
    "79231":	3,
    "8250":	    2,
    "8250CE":	2,
    "8250SD":	2,
    "L5795":	2.5,
    "L65051":	3,
    "L7535":	3,
    "L7540":	1.5,
    "L7573":	3,
    "L7581":	3,
    "L7594":	3,
    "L7601":	3,
    "L7614":	3,
    "L8000":	2,
    }
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
        credit_hours = course_hourse_translation_dict.get(cn, None)
        if credit_hours is None:
            core.log(f"Course CN {cn} not found in translation dictionary. Skipping.")
            continue
        update_his_record(pid, cn, sq, credit_hours)
        pass
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