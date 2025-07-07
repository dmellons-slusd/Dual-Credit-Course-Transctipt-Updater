from pandas import read_sql_query, DataFrame
from slusdlib import aeries, core, decorators

sql = core.build_sql_object()
cnxn = aeries.get_aeries_cnxn(database="DST24000SLUSD_DAILY", access_level='w')
def update_his_record(pid: int, cn: str, sq: str, credit_hours: int = 1.5) -> None:
    update_sql = sql.update_his_dual_credit.format(
        pid=pid,
        cn=cn,
        sq=sq,
        credit_hours=credit_hours
    )
    core.log(f"Updating HIS record for PID: {pid}, CN: {cn}, SQ: {sq}")
    core.log(update_sql)

@decorators.log_function_timer
def update_dual_credit_hist():
    data = read_sql_query(sql.dual_credit_courses, cnxn)
    print(data.head())
    for index, row in data.iterrows():
        pid = row['PID']
        cn = row['CN']
        sq = row['SQ']
        # print(f'{pid, cn, sq}')
        update_his_record(pid, cn, sq)
        pass

if __name__ == "__main__":
    core.log("~"*80)
    core.log(f"Starting update_dual_credit_hist")
    update_dual_credit_hist()
    core.log("~"*80)