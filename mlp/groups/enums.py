from arcutils import ChoiceEnum

class UserRole(ChoiceEnum):
    """
    User roles as determined by their class.
    """    
    RESEARCHER = 1
    STUDENT = 2
    ADMIN = 4
    TA = 8

    _choices = (
        (RESEARCHER, "Researcher"),
        (STUDENT, "Student"),
        (ADMIN, "Admin"),
        (TA, "Teachers Assistant"),
    )
