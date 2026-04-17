from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class _FakeResponse:
    output_text: str


class FakeResponsesAPI:
    def __init__(self, responder):
        self._responder = responder

    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        text: dict,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict | None = None,
    ):
        payload = json.loads(input)
        fmt = text.get("format", {})
        schema_name = fmt.get("name")
        out = self._responder(schema_name=schema_name, instructions=instructions, payload=payload, metadata=metadata or {})
        return _FakeResponse(output_text=json.dumps(out))


class FakeOpenAIClient:
    def __init__(self, responder):
        self._responses = FakeResponsesAPI(responder)

    @property
    def responses(self) -> FakeResponsesAPI:
        return self._responses


def default_responder(*, schema_name: str, instructions: str, payload: dict[str, Any], metadata: dict[str, Any]) -> dict:
    """Default fake responder. Detects Russian language from payload and returns Russian strings."""
    lang = (payload.get("brand_profile") or {}).get("content_language", "en")
    return _respond(schema_name=schema_name, payload=payload, lang=lang)


def russian_responder(*, schema_name: str, instructions: str, payload: dict[str, Any], metadata: dict[str, Any]) -> dict:
    """Fake responder that always returns Russian content (for language-pivot tests)."""
    return _respond(schema_name=schema_name, payload=payload, lang="ru")


def _respond(*, schema_name: str, payload: dict[str, Any], lang: str) -> dict:
    if schema_name == "DayPlanPayload":
        if lang == "ru":
            return {
                "day": payload["day"],
                "items": [
                    {
                        "slot": 1,
                        "format": "post",
                        "primary_angle": "заземлённое размышление + одно действие",
                        "creative_brief": "Переведи самый сильный сигнал в практическую проверку и 3-шаговое микро-действие.",
                        "signal_keys": [payload["astro_day"]["signals"][0]["key"]],
                        "content_pillar": "Образование",
                        "face_led_preference": False,
                    },
                    {
                        "slot": 2,
                        "format": "reel",
                        "primary_angle": "быстрое руководство что делать / чего не делать",
                        "creative_brief": "Быстрый список, избегающий абсолютизма, с успокаивающим призывом.",
                        "signal_keys": [payload["astro_day"]["signals"][1]["key"]],
                        "content_pillar": "Мотивация",
                        "face_led_preference": True,
                    },
                ],
                "notes": ["Сохраняй тон полезным; избегай предсказаний."],
            }
        return {
            "day": payload["day"],
            "items": [
                {
                    "slot": 1,
                    "format": "post",
                    "primary_angle": "grounded reflection + one action",
                    "creative_brief": "Translate the strongest signal into a practical check-in and a 3-step micro-action.",
                    "signal_keys": [payload["astro_day"]["signals"][0]["key"]],
                    "content_pillar": "Education",
                    "face_led_preference": False,
                },
                {
                    "slot": 2,
                    "format": "reel",
                    "primary_angle": "quick do/don't guidance",
                    "creative_brief": "A fast list that avoids absolutism, with a calming CTA.",
                    "signal_keys": [payload["astro_day"]["signals"][1]["key"]],
                    "content_pillar": "Motivation",
                    "face_led_preference": True,
                },
            ],
            "notes": ["Keep tone helpful; avoid predictions."],
        }

    if schema_name == "PostDraftPayload":
        if lang == "ru":
            return {
                "title": "Транзит дня: простой перезапуск",
                "hook": "Если голова сегодня гудит — вот 60-секундный перезапуск.",
                "caption": "Вот заземлённый способ работать с этой энергией:\n\n— Назови, что тебя тянет назад\n— Выбери одно маленькое следующее действие\n— Закрой один незавершённый вопрос\n\nНе нужно ничего форсировать. Просто сделай чуть легче.",
                "cta": "Сохрани на потом и напиши в комментах: перезапуск — если хочешь продолжение.",
                "hashtags": ["#астрология", "#осознанность", "#ежедневныйритуал"],
                "voice_note": "Тёплый, прямой тон под пресет educational_warm.",
                "metadata": {},
            }
        return {
            "title": "Today's transit: a simple reset",
            "hook": "If your brain feels loud today, try this 60-second reset.",
            "caption": "Here's a grounded way to work with the energy:\n\n- Name what's pulling you\n- Pick one small next step\n- Close the loop with one supportive boundary\n\nYou don't need to force it. Just make it easier.",
            "cta": "Save this for later and comment: reset if you want a part 2.",
            "hashtags": ["#astrology", "#mindset", "#dailyritual"],
            "voice_note": "Warm, direct tone to match educational_warm preset.",
            "metadata": {},
        }

    if schema_name == "ReelDraftPayload":
        if lang == "ru":
            return {
                "hook_0_3s": "Твой мозг солгал тебе сегодня.",
                "hook": "Твой мозг солгал тебе сегодня — и вот как это поймать.",
                "reel_type": "talking_head",
                "on_screen_text": ["Твой мозг солгал", "Поймай за 20 секунд", "Вот перезапуск"],
                "script": "Быстрая проверка: что одно ты можешь упростить сегодня? Выбери один маленький следующий шаг, потом закрой один вопрос. Всё. Ты строишь импульс, не форсируя.",
                "cta": "Подпишись на ежедневные транзиты.",
                "metadata": {},
            }
        return {
            "hook_0_3s": "Your brain lied to you today.",
            "hook": "Your brain lied to you today — and here's how to catch it.",
            "reel_type": "talking_head",
            "on_screen_text": ["Your brain lied to you", "Catch it in 20 seconds", "Here's the reset"],
            "script": "Quick check-in: What's the one thing you can simplify today? Pick one small next step, then close one loop. That's it. You're building momentum without forcing it.",
            "cta": "Follow for tomorrow's check-in.",
            "metadata": {},
        }

    raise AssertionError(f"Unexpected schema_name: {schema_name}")
