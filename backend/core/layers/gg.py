import base64 
import os
from google import genai 
from google.genai import types

def generate():
    client = genai.client(
        api_key=os.environ.get("GEMINI_API_KEY")
    )

    model = "gemini-2.5-flash-preview-05-20"
    contents = [
        types.content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT INPUT HERE"""),
            ]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain", 
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()