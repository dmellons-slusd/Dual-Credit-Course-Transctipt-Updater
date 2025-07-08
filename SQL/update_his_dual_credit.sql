update his
set 
    SDE = :sde,
    CH = :credit_hours,
    ST = :st
where
    del = 0
    and PID = :pid
    and CN = :cn
    and SQ = :sq;
