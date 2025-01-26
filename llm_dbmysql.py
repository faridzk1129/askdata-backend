import os
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from werkzeug.exceptions import BadRequest
from prompts import examples, example_prompt, answer_prompt
from pyexcelerate import Workbook

def main_llm(question: str, session: str = None):
    df_to_dict = []
    sql_query = ""

    # Load environment variables
    load_dotenv()

    os.getenv("OpenAI_API_KEY")
    # Connect to database
    mysql_uri = os.getenv("DATABASE_URI")
    engine = create_engine(mysql_uri)

    include_tables = ["data_produksi"]

    # Read database
    db = SQLDatabase(engine=engine).from_uri(
        mysql_uri, include_tables=include_tables
    )
    
    # Ambil model dari environment variable jika tidak di set up maka defaultnya model gpt-4o-mini
    model_name = os.getenv("MODEL_NAME") if os.getenv("MODEL_NAME") is not None else "gpt-4o-mini"

    # Setup the model (ChatOpenAI)
    llm = ChatOpenAI(model=model_name, temperature=0)

    try:
        validation_prompt(question)

        # Generate SQL query
        sql_query = create_query(llm, db, question)

        sql_query = formatting_query(sql_query, question)
        print(sql_query)

        # Convert query result to excel
        df_to_dict, df_to_dict_length = convert_query_to_excel(
            sql_query, engine, session
        )

        def provide_query(input):
            return {"query": sql_query}

        def provide_result(input):
            return {"result": df_to_dict}

        def provide_question(input):
            return {"question": question}

        def provide_df_to_dict_length(input):
            return {"df_to_dict_length": df_to_dict_length}

        # Setup chain
        chain_to_natural_language = (
            RunnablePassthrough.assign(question=provide_question)
            .assign(query=provide_query)
            .assign(df_to_dict_length=provide_df_to_dict_length)
            .assign(result=provide_result)
            | answer_prompt
            | llm
            | StrOutputParser()
        )

        # Validate and execute the chain
        if validation_query(sql_query):
            # Execute the chain with the user input question
            natural_language = chain_to_natural_language.invoke(
                {"input": question, "df_to_dict_length": df_to_dict_length}
            )
    except Exception as e:
        print(str(e))
        natural_language = str(e)

    return natural_language, df_to_dict, sql_query


def validation_query(query):
    ignore_keywords = [
        "DELETE",
        "UPDATE",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "REPLACE",
        "MERGE",
        "INSERT",
        "LOCK TABLES",
        "UNLOCK TABLES",
        "TABLES",
        "DATABASES",
        "DROP",
        "SET",
    ]

    # Convert the query to uppercase and check whether it contains prohibited keywords
    for keyword in ignore_keywords:
        if keyword in query.upper():
            raise BadRequest("Perintah yang dimasukkan tidak diizinkan")

    # Limits the tables that can be accessed
    include_table = ["data_produksi"]
    for keyword in include_table:
        if keyword not in query:
            raise BadRequest("Akses pada data tersebut tidak diizinkan")

    return True


def validation_prompt(question):
    ignore_word = [
        "hapus",
        "edit",
        "ubah",
        "replace",
        "prediksi",
        "perkiraan",
        "delete",
        "ganti",
        "tambah",
        "input",
        "simpan",
        "buat",
        "modifikasi",
        "setel",
        "ganti nama",
        "formulasikan",
        "masukkan",
        "perbarui",
        "revisi",
        "sunting",
        "transfer",
        "perkaya",
        "koreksi",
        "filter",
        "ekspor",
        "impor",
    ]

    if question == "":
        raise BadRequest("Perintah tidak boleh kosong")
    
    # Change the query to uppercase and check whether it contains prohibited keywords
    for keyword in ignore_word:
        if keyword in question.lower():
            raise BadRequest("Perintah yang dimasukkan tidak diizinkan")

    return True


def is_data_not_null(df):
    if df == []:
        raise ValueError("Data yang diminta tidak ditemukan di dalam database")
    return True


def formatting_query(raw_query, question):
    # Convert response to string if it is not already
    if not isinstance(raw_query, str):
        raw_query = str(raw_query)

    # Remove keyword
    formatted_query = (
        raw_query.replace("SQLQuery:", "")
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

    # Remove question string in query result
    if (
        question.lower() in formatted_query.lower()
        or "question:" in formatted_query.lower()
    ):
        formatted_query = formatted_query.replace(question, "").strip()
        formatted_query = formatted_query.replace("Question:", "").strip()

    keyword_list = ["SHOW", "DESCRIBE", "EXPLAIN", "SELECT"]
    for keyword in keyword_list:
        index = formatted_query.find(keyword)
        if index != -1:
            # Find (;) after keyword
            semicolon_index = formatted_query.find(";", index)

            # If a semicolon is found, retrieve the text from the keyword to the semicolon
            formatted_query = formatted_query[index : semicolon_index + 1] if semicolon_index != -1 else formatted_query[index:]
                
            break
    return formatted_query


def convert_query_to_excel(query, engine, session):
    try:
        if validation_query(query):
            # Create dataframe from query result
            df = pd.read_sql(query, engine)
            if len(df) > 1:
                df.insert(loc=0, column="No.", value=range(1, len(df) + 1))

            # Keyword for filter column
            keyword_show_table = ["SHOW", "DESCRIBE", "EXPLAIN", "`COLUMN_NAME`"]

            # Check if the excel file is available
            for keyword in keyword_show_table:
                if keyword in query.upper():
                    df = df.drop(columns=["Type", "Null", "Key", "Default", "Extra"])
                    break

            # Convert dataframe to dictionary
            df_to_dict = df.head(7).to_dict(
                orient="records",
            )

            df_to_dict_length = len(df_to_dict)
            
            # Make excel file            
            if is_data_not_null(df_to_dict):
                # convert dataframe into list format
                data = [df.columns.tolist()] + df.values.tolist()  # Menambahkan header

                # create workbook and write code to excel
                wb = Workbook()
                wb.new_sheet("Sheet1", data=data)
                wb.save(f"excel_data/{session}.xlsx")
            
            return df_to_dict, df_to_dict_length
    except Exception as e:
        raise Exception(str(e))


def create_query(llm, db, question):
    try:
        prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            prefix="You are a MYSQL expert. Given an input question, create a syntactically correct MYSQL query to run. Unless otherwise specified, do not return more than {top_k} rows..\n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries.",
            suffix="User input: {input}\nSQL query: ",
            input_variables=["input", "top_k", "table_info"],
        )

        # Initialize the query generation chain
        chain_to_create_query = create_sql_query_chain(
            llm,
            db,
            prompt,
        )

        # Generate the SQL query
        response = chain_to_create_query.invoke(
            {"question": question, "top_k": 10, "table_info": "data_produksi"}
        )

        # Format query
        sql_query = formatting_query(response, question)
        return sql_query
    except Exception as e:
        raise Exception("Terjadi kesalahan saat membuat query")