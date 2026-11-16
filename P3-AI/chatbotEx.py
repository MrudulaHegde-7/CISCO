import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


load_dotenv(Path(__file__).with_name(".env"))


@asynccontextmanager
async def lifespan(app: FastAPI):
	api_key = os.getenv("GEMINI_API_KEY")
	client = genai.Client(
		api_key=api_key,
		http_options=types.HttpOptions(
			timeout=60000,
			retry_options=types.HttpRetryOptions(attempts=1),
		),
	) if api_key else None
	app.state.gemini_client = client
	try:
		yield
	finally:
		if client:
			await client.aio.aclose()
			client.close()


app = FastAPI(title="Gemini Chat", lifespan=lifespan)


class ChatMessage(BaseModel):
	role: Literal["user", "model"]
	content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
	question: str = Field(min_length=1, max_length=4000)
	history: list[ChatMessage] = Field(default_factory=list, max_length=30)


@app.get("/", include_in_schema=False)
async def frontend():
	return FileResponse(Path(__file__).parent / "frontend" / "chat.html")


@app.post("/chat")
async def chat(data: ChatRequest):
	client = app.state.gemini_client
	if client is None:
		raise HTTPException(
			status_code=503,
			detail="GEMINI_API_KEY is missing. Add it to your .env file and restart the app.",
		)

	conversation = [
		f"{'User' if message.role == 'user' else 'Assistant'}: {message.content}"
		for message in data.history
	]
	conversation.append(f"User: {data.question}")

	try:
		reply = await asyncio.wait_for(
			client.aio.interactions.create(
				model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
				input="\n\n".join(conversation),
				generation_config={"thinking_level": "low"},
				store=False,
			),
			timeout=65,
		)
	except TimeoutError as error:
		raise HTTPException(status_code=504, detail="Gemini request timed out. Please try again.") from error
	except genai.errors.APIError as error:
		if error.code in (429, 503):
			raise HTTPException(
				status_code=error.code,
				detail="Gemini is busy or its quota has been reached. Please try again later.",
			) from error
		if error.code == 504:
			raise HTTPException(status_code=504, detail="Gemini request timed out. Please try again.") from error
		raise HTTPException(status_code=502, detail="Gemini could not answer this request. Check the configured model and API access.") from error
	except Exception as error:
		status = getattr(error, "status_code", None)
		if status in (429, 503):
			raise HTTPException(
				status_code=status,
				detail="Gemini is busy or its quota has been reached. Please try again later.",
			) from error
		if status == 504:
			raise HTTPException(status_code=504, detail="Gemini request timed out. Please try again.") from error
		raise HTTPException(status_code=502, detail="Could not reach Gemini. Please try again.") from error

	if not reply.output_text:
		raise HTTPException(status_code=502, detail="Gemini returned no answer.")

	return {"answer": reply.output_text}
