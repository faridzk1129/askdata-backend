# Ask-Data  


# In this repo only the backend side, you can find the frontend side of askdata in my other repo

Ask-Data is a web application designed using modern technologies such as FastAPI, Next.js, Langchain (leveraging the ChatGPT API), Docker, Python, MySQL, and TailwindCSS.  

This application operates similarly to ChatGPT, allowing users to ask natural language questions related to company data, such as:  
*"What was the total revenue from marketing campaigns during the last quarter?"*  

### How It Works:  
1. The user submits a question in natural language.  
2. The LLM model converts the question into an SQL query.  
3. The SQL query retrieves data from the company's database.  
4. The retrieved data is then transformed back into human-readable language.  

This application aims to simplify the process of exploring and understanding company data efficiently, without requiring users to have knowledge of SQL or database structures.  

### Set Up Application  

Follow these steps to set up the application:  

```bash
# 1. Remove any existing virtual environment
rm -rf .venv  

# 2. Create a new virtual environment
python -m venv .venv  

# 3. Activate the virtual environment
source .venv/bin/activate  

# 4. Install dependencies
pip install -r requirements.txt  

# 5. Run the application
uvicorn main:app --reload  # askdata-backend
