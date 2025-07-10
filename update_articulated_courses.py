from pandas import DataFrame, read_sql_query
from slusdlib import aeries, core, decorators
from course_hour_mappings import COURSE_HOURS_MAPPING, get_course_hours
from sqlalchemy import bindparam, text
from decouple import config

SQL = core.build_sql_object()
CNXN = aeries.get_aeries_cnxn(database=config('DATABASE', cast=str), access_level='w') if config('TEST', cast=bool) == False else aeries.get_aeries_cnxn(database=config('TEST_DATABASE', cast=str), access_level='w')

@decorators.log_function_timer
def update_articulated_courses() -> None:
    """
    Update CRS records for articulated courses based on course mappings.
    """
    articulated_courses: list[str] = list(COURSE_HOURS_MAPPING.keys())
    
    # Update college credit only courses
    college_credit_only_courses: list[str] = [
        '4141',
        '4142'
    ]
    
    with CNXN.connect() as conn:

        try:
            sql_statement = text(SQL.update_articulated_courses_bulk).bindparams(
                bindparam("cn_list", expanding=True)
            )
            result = conn.execute(
                sql_statement,
                {
                    "cl": 24,
                    "cn_list": articulated_courses
                }
            )
            conn.commit()
            core.log(f"Updated {result.rowcount} articulated courses to CL = 24.")
        except Exception as e:
            core.log(f"Error updating articulated courses: {e}")
            raise

        
        try:
            sql_statement = text(SQL.update_articulated_courses_bulk).bindparams(
                bindparam("cn_list", expanding=True)
            )
            result = conn.execute(
                sql_statement,
                {
                    "cl": 23,
                    "cn_list": college_credit_only_courses
                }
            )
            conn.commit()
            core.log(f"Updated {result.rowcount} college credit only courses to CL = 23.")
        except Exception as e:
            core.log(f"Error updating college credit only courses: {e}")
            raise
if __name__ == "__main__":
    update_articulated_courses()