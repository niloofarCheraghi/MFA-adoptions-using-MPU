from pydantic import BaseModel, Field

class User(BaseModel):
    firstname: str | None = Field(None)
    lastname: str | None = Field(None)
    email: str = Field(...)
    is_verified: bool = Field(default=False)
    chat_id: int | None = Field(None)
    telegram_username: str | None = Field(None)
    secret_key: str | None = Field(None)
    current_otp: str | None = Field(None)
    otp_expiry: float | None = Field(None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "firstname": "Joseph`",
                "lastname": "Joe",
                "email": "example@gmail.com",
                "telegram_username": "josephINTT"
            }
        }



    


    