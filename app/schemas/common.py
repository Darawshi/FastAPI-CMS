#app/schemas/common.py
from pydantic import StringConstraints, Field
from typing_extensions import Annotated

PasswordType = Annotated[
    str,
    StringConstraints(
        min_length=8,
        pattern=r"[A-Za-z\d@$!%*?&]*[A-Z]+[A-Za-z\d@$!%*?&]*[a-z]+[A-Za-z\d@$!%*?&]*\d+[A-Za-z\d@$!%*?&]*[@$!%*?&]+[A-Za-z\d@$!%*?&]*"
    ),
    Field(
        description="Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character.",
    )
]