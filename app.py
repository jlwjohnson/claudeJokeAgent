import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Claude Joke Agent")

VALID_JOKE_TYPES = {"dad", "animal", "kid"}

SYSTEM_PROMPT = """You are a friendly joke-telling agent. When asked for a joke, you tell exactly ONE joke
of the requested type. Keep it short, clean, and funny. Just tell the joke — no preamble or commentary."""


class JokeRequest(BaseModel):
    joke_type: str


class JokeResponse(BaseModel):
    joke_type: str
    joke: str


def _generate_joke(joke_type: str) -> JokeResponse:
    joke_type = joke_type.lower().strip()

    if joke_type not in VALID_JOKE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid joke_type '{joke_type}'. Must be one of: {', '.join(sorted(VALID_JOKE_TYPES))}",
        )

    client = anthropic.AnthropicBedrock()

    message = client.messages.create(
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Tell me a {joke_type} joke."}],
    )

    return JokeResponse(joke_type=joke_type, joke=message.content[0].text)


@app.get("/joke", response_model=JokeResponse)
def get_joke(joke_type: str = "dad"):
    return _generate_joke(joke_type)


@app.post("/joke", response_model=JokeResponse)
def post_joke(request: JokeRequest):
    return _generate_joke(request.joke_type)


@app.get("/health")
def health():
    return {"status": "ok"}
