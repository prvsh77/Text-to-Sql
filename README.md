# 🧠 Text-to-SQL – Natural Language to Database Query Generator

Text-to-SQL is an AI-powered system that converts **natural language questions into executable SQL queries**, enabling users to interact with databases without writing SQL manually.

The project demonstrates the integration of **NLP, query generation logic, and interactive data exploration** through a clean, user-friendly interface.

---

## 🚧 Problem

Accessing databases typically requires knowledge of SQL, which creates a barrier for non-technical users and slows down exploratory analysis.

Manual query writing can also be:
- Error-prone
- Time-consuming
- Difficult to scale for ad-hoc queries

---

## 💡 Solution

Text-to-SQL bridges this gap by allowing users to:
- Ask questions in plain English
- Automatically generate corresponding SQL queries
- Execute queries against a database
- View results instantly in an interactive UI

---

## ✨ Key Features

- Converts natural language questions into valid **SQL statements**
- Uses **spaCy NLP pipeline** for parsing and entity recognition
- Connects to an **SQLite** sample database for execution
- Displays both:
  - Generated SQL query
  - Query results in tabular form
- Interactive **Streamlit UI** for real-time testing
- Modular design, extensible to other databases (MySQL, PostgreSQL, etc.)

---

## 🧠 System Design (High Level)

- **User Input Layer** – Accepts natural language queries  
- **NLP Processing Engine** – Extracts intent, entities, and conditions  
- **Query Generator** – Maps parsed intent to SQL templates  
- **Database Layer** – Executes SQL against SQLite  
- **UI Layer** – Displays SQL and results dynamically  

The system emphasizes **interpretability and correctness** over black-box generation.

---

## 🛠️ Technology Stack

| Category | Tools |
|------|------|
| Language | Python |
| NLP | spaCy |
| Database | SQLite |
| UI | Streamlit |
| Data Handling | Pandas |

---

## 🚀 How to Run

```bash
git clone https://github.com/prvsh77/Text-to-Sql.git
cd Text-to-Sql
pip install -r requirements.txt
streamlit run app.py
