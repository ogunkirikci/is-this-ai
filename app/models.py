from pydantic import BaseModel, HttpUrl, Field
from typing import Literal, Optional

MediaType = Literal["image", "video"]

class EnqueueRequest(BaseModel):
    tweet_id: str = Field(..., description="Mention tweet id (the tweet that tagged the bot)")
    author_id: str = Field(..., description="User id of the mention author")
    reply_to_tweet_id: str = Field(..., description="The tweet id you will reply to (usually mention tweet)")
    media_url: HttpUrl = Field(..., description="Direct URL to media (image/video variant)")
    media_type: MediaType

    # optional context
    quoted_tweet_id: Optional[str] = None
    original_tweet_id: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
