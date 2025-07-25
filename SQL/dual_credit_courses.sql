select
    his.*
from his
join stu on his.pid = stu.id and stu.del = 0 and stu.tg = ''
where his.del = 0
    AND his.gr in (9,10,11,12)
    AND his.cn in ( 
'3160', 
'4141', 
'4142', 
'4671', 
'5343', 
'5361', 
'6608AC', 
'6614AC', 
'6615AC', 
'75341', 
'75351', 
'75361', 
'75371', 
'75501', 
'75511', 
'75551', 
'75552', 
'75554', 
'75701', 
'75702', 
'75712', 
'75801', 
'75811', 
'75941', 
'75951', 
'76011', 
'76012', 
'76051', 
'76052', 
'76071', 
'76081', 
'76141', 
'76151', 
'76241', 
'76251', 
'79102', 
'79201', 
'79211', 
'79212', 
'79220', 
'79221', 
'79230', 
'79231', 
'79310', 
'8250', 
'8250CE', 
'8250SD', 
'CCC289', 
'L5795', 
'L65051', 
'L7532', 
'L7535', 
'L7540', 
'L7551', 
'L7572', 
'L7573', 
'L7581', 
'L7594', 
'L7601', 
'L76071', 
'L7614', 
'L8000', 
'T75361'
)

order by his.yr desc,  his.pid, his.te asc