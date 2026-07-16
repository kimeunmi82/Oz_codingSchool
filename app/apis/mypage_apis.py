from fastapi import APIRouter, HTTPException, status, Path
from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints
import re
from typing import Annotated


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/mypage_api")

#####################################################
# 2. API Endpoints 구현
#####################################################