from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel
from enum import Enum

class Choice(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class Answer(BaseModel):
    Question_1: List[Choice]
    Question_2: List[Choice]
    Question_3: List[Choice]
    Question_4: List[Choice]
    Question_5: List[Choice]