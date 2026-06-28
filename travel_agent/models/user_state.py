from __future__ import annotations

from pydantic import BaseModel, Field


class UserState(BaseModel):
    """用户在旅行时刻的状态画像"""

    location: str = Field(
        default="",
        description="用户当前所在城市或区域，例如'杭州西湖区'",
    )
    mood: int = Field(
        default=5,
        ge=1,
        le=10,
        description="心情指数，1=很低落，10=很兴奋",
    )
    fatigue: int = Field(
        default=5,
        ge=1,
        le=10,
        description="疲惫度，1=精力充沛，10=极度疲惫",
    )
    curiosity: int = Field(
        default=5,
        ge=1,
        le=10,
        description="好奇心，1=只想躺平，10=渴望探索一切",
    )
    budget: str = Field(
        default="",
        description="预算约束，例如'人均200以内'或'无限制'",
    )
    companion: str = Field(
        default="",
        description="同行者，例如'独自'、'情侣'、'带娃'、'朋友'",
    )
    preferences: str = Field(
        default="",
        description="偏好标签，例如'自然风光、美食、避开人多'",
    )

    def summary(self) -> str:
        parts = [
            f"📍 位置：{self.location}",
            f"😊 心情：{self.mood}/10",
            f"😫 疲惫：{self.fatigue}/10",
            f"🔍 好奇：{self.curiosity}/10",
        ]
        if self.budget:
            parts.append(f"💰 预算：{self.budget}")
        if self.companion:
            parts.append(f"👥 同行：{self.companion}")
        if self.preferences:
            parts.append(f"💡 偏好：{self.preferences}")
        return "\n".join(parts)

    def is_ready(self) -> bool:
        """是否已收集到足够信息来生成计划"""
        return bool(self.location)
