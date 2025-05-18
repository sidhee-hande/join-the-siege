from werkzeug.datastructures import FileStorage
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import os
import io
import tiktoken
import time
from functools import wraps
from src.text_extractors import extract_text_from_csv, extract_text_from_docx,extract_text_from_image,extract_text_from_pdf,extract_text_from_txt,extract_text_from_xls,extract_text_from_xlsx



load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result, cost = func(*args, **kwargs)
        except Exception as e:
            return {"error": str(e)}, 0, time.time() - start
        elapsed = time.time() - start
        return result, cost, elapsed
    return wrapper


@time_it
def classify_file(file: FileStorage):
    filename = file.filename.lower()
    file_stream = io.BytesIO(file.read())

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_stream)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file_stream)
        elif filename.endswith(".txt"):
            text = extract_text_from_txt(file_stream)
        elif filename.endswith((".jpg", ".png", ".jpeg")):
            text = extract_text_from_image(file)
        elif filename.endswith(".xlsx"):
            text = extract_text_from_xlsx(file_stream)
        elif filename.endswith(".xls"):
            text = extract_text_from_xls(file_stream)
        elif filename.endswith(".csv"):
            text = extract_text_from_csv(file_stream)
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        raise RuntimeError(f"Failed to extract text: {str(e)}")

    if not text.strip():
        raise ValueError("No extractable text found in the file.")

    return document_identifier(text)

def document_identifier(document_text: str):
    model = "gpt-3.5-turbo"
    max_context = 4096
    reserved_tokens = 200  # reserve for system/user overhead and response
    max_input_tokens = max_context - reserved_tokens

    try:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")

        system_prompt = (
            "You are a document classification assistant. Given a document's text content, "
            "identify what type of document it is. Respond with only the name of the document."
        )
        user_prefix = "What type of document is this?\n\n"

        # Token counts for fixed message parts
        system_tokens = len(encoding.encode(system_prompt))
        prefix_tokens = len(encoding.encode(user_prefix))

        # Tokenize and truncate document text
        doc_tokens = encoding.encode(document_text)
        max_doc_tokens = max_input_tokens - system_tokens - prefix_tokens

        if max_doc_tokens <= 0:
            raise ValueError("Document too long to classify after reserving context space.")

        truncated_doc_tokens = doc_tokens[:max_doc_tokens]
        truncated_text = encoding.decode(truncated_doc_tokens)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prefix}{truncated_text}"}
        ]

        input_tokens = count_tokens(messages, model)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=150
        )

        output_tokens = response.usage.completion_tokens

        # Pricing
        cost_per_1k_input = 0.0005
        cost_per_1k_output = 0.0015

        input_cost = (input_tokens / 1000) * cost_per_1k_input
        output_cost = (output_tokens / 1000) * cost_per_1k_output
        total_cost = input_cost + output_cost
        cost_in_microdollars = int(total_cost * 1_000_000)

        doc_type = response.choices[0].message.content.strip()
        return doc_type, cost_in_microdollars

    except OpenAIError as oe:
        raise RuntimeError(f"OpenAI API error: {oe}")
    except ValueError as ve:
        raise RuntimeError(f"Value error during document classification: {ve}")
    except Exception as e:
        raise RuntimeError(f"Document classification failed: {e}")


def count_tokens(messages, model="gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")  # fallback
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message has some overhead
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    num_tokens += 2  # priming tokens
    return num_tokens
