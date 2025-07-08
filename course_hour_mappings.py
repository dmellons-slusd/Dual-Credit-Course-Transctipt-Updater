COURSE_HOURS_MAPPING = {
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

def get_course_hours(course_number) -> float:
    """
    Get credit hours for a course number.
    
    Args:
        course_number (str): The course number to look up
        
    Returns:
        float: Credit hours for the course, or None if not found
    """
    return COURSE_HOURS_MAPPING.get(course_number, None)

def get_all_courses():
    """Return all course numbers that have mappings."""
    return list(COURSE_HOURS_MAPPING.keys())