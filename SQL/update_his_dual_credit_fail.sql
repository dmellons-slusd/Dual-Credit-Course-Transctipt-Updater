update his
set 
    SDE = :sde,
    ST = :st
where
    del = 0
    and PID = :pid
    and CN = :cn
    and SQ = :sq;