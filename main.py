from fastapi import FastAPI, HTTPException, Response, Header
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm_dbmysql import main_llm, validation_query, is_data_not_null, validation_prompt
from fastapi.responses import FileResponse
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.exceptions import BadRequest
from fastapi import HTTPException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Adjust this in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# create log directory if not any
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Add TimedRotatingFileHandler for log rotation
log_file = os.path.join(log_directory, "activity.log")
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30)
handler.suffix = "%Y-%m-%d"  

# Add formatter which like basicConfig
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to Logger
logger.addHandler(handler)

# Ambil model dari environment variable
model_info = os.getenv("MODEL_NAME") if os.getenv("MODEL_NAME") is not None else "gpt-4o-mini"
logger.info(f"Model use: {model_info}")

# Request and Response schema
class QueryRequest(BaseModel):
    question: str


class QueryData(BaseModel):
    natural_language: str
    table_show_web: list = []
    table_excel: str | None = None


class QueryResponse(BaseModel):
    status_code: int
    message: str
    data: QueryData = None


def show_logging_error(query, error):
    logger.error(f"Query execution failed: {query} - Error: {str(error)}")


# Endpoint POST for get question and give the answer from model
@app.post("/ask", response_model=QueryResponse)
async def ask_query(
    request: QueryRequest,
    response: Response,
    x_session_id: Annotated[str | None, Header(alias="X-Session-ID")] = None,
):
    # Check x_session_id is available?
    if x_session_id is None:
        response.status_code = 400
        raise HTTPException(detail="X-Session-ID header is required")
    
    # Processing question with LLM model
    natural_language, table_show_web, sql_query = main_llm(
        request.question, session=x_session_id
    )

    file_url = ""

    logger.info(f"Question: {request.question}")
    logger.info(f"Query: {sql_query}")

    try:
        validation_prompt(request.question)

        if sql_query == "":
            raise ValueError("Terjadi kesalahan teknis")

        if validation_query(sql_query):
            if is_data_not_null(table_show_web):
                # set temporary file and file nime
                temp_file = f"excel_data/{x_session_id}.xlsx"
                file_name = f"{x_session_id}.xlsx"

                # Check whether the Excel file was created successfully
                if not os.path.exists(temp_file):
                    raise ValueError("File Excel tidak ditemukan.")

                # URL to download excel file
                file_url = f"/download/{file_name}"

                # set status code success
                response.status_code = 200

                # Make logging
                logger.info(f"Query executed successfully: {response.status_code} - {sql_query}")

                # Mengirimkan response sukses
                return QueryResponse(
                    status_code=200,
                    message="Success",
                    data=QueryData(
                        natural_language=natural_language,
                        table_show_web=table_show_web,
                        table_excel=file_url,
                    ),
                )

    except BadRequest as e:
        show_logging_error(sql_query, e)
        response.status_code = 400
        return QueryResponse(
            status_code=400,
            message=natural_language,
            data=QueryData(
                natural_language=natural_language,
            ),
        )

    except ValueError as e:
        show_logging_error(sql_query, e)
        response.status_code = 404
        return QueryResponse(
            status_code=404,
            message=str(e),
            data=QueryData(
                natural_language=str(e),
            ),
        )
    except HTTPException as e:
        # If any exception from FastAPI, use status code and error detail from Exception
        show_logging_error(sql_query, e)
        response.status_code = 400
        return QueryResponse(
            status_code=400,
            message=str(e),
            data=QueryData(
                natural_language=str(e),
            ),
        )

    except Exception as e:
        # If another error occurs, return status code 500 and error details
        show_logging_error(sql_query, e)
        response.status_code = 500
        return QueryResponse(
            status_code=500,
            message=str(e),
            data=QueryData(
                natural_language=str(e),
            ),
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to the LLM API"}

# Add new endpoint for file download  
@app.get("/download/{file_name}")
async def download_file(file_name: str):
    # path excel file
    file_path = f"excel_data/{file_name}"

    # check if the excel file is available
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")

    return FileResponse(file_path, filename=file_name)