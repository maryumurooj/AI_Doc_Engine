

#AI-Powered Financial Document Ingestion & Analysis Engine

> Ingest. Structure. Analyze. Summarize — all offline.

This project lets you upload financial documents (like PDF balance sheets or income statements), parse them, extract structured data using LLMs (e.g., Deepseek R1), store them in a MySQL database, compare performance over time, and generate human-like summaries.

---

## 📦 Features

- 🔍 **PDF Parsing** with `pdfplumber`
- 🧠 **LLM-Powered Extraction** using LangChain & Ollama (Deepseek R1 / Mistral / LLaMA3)
- ✅ **Pydantic Validation** of structured financial fields
- 🗃️ **MySQL Database Storage** (via SQLAlchemy)
- 📈 **Trend Analysis** across years (RAG-style)
- 📝 **Auto-generated Summaries** like "Net income grew 25% YoY"
- 🌐 **FastAPI-based REST Endpoints**
- 🧩 Fully **offline-capable** — no OpenAI or cloud APIs required

---

## 🏗️ Architecture

```text
[ PDF Upload ] → [ Parse Text ] → [ LLM + Prompt (LangChain) ]
    ↓                     ↓
[ Pydantic Validation ] → [ Store in MySQL ]
    ↓
[ Trend Comparison ] → [ Summary via LLM ]
````

---

## ⚙️ Tech Stack

| Layer           | Tech                           |
| --------------- | ------------------------------ |
| Backend API     | FastAPI                        |
| PDF Parsing     | pdfplumber                     |
| LLM Interface   | LangChain + Ollama             |
| Local Models    | Deepseek R1 / Mistral / LLaMA3 |
| ORM/DB          | SQLAlchemy + MySQL             |
| Validation      | Pydantic                       |
| Vector DB (opt) | Chroma + Sentence Transformers |

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/maryumurooj/financial-ai-ingestor.git
cd financial-ai-ingestor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> You’ll also need to install [Ollama](https://ollama.com):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama run deepseek-coder:7b-instruct
```

### 3. Setup MySQL

Create a database and update your `.env`:

```env
DB_URL=mysql+pymysql://username:password@localhost/financialdb
```

### 4. Start the Server

```bash
uvicorn main:app --reload
```

---

## 🛠️ API Endpoints

### 📥 Upload & Ingest PDF

```http
POST /ingest
```

* Uploads a financial PDF
* Extracts and validates financial fields
* Saves to MySQL

### 📊 Compare Company Performance

```http
GET /compare/{company_name}
```

* Fetches last 2 years of data for a company
* Generates a natural language summary via LLM

---

## 🧠 Supported Models (via Ollama)

| Model            | Description                           |
| ---------------- | ------------------------------------- |
| `deepseek-coder` | Best for structured data + reasoning  |
| `mistral`        | Fast, general-purpose LLM             |
| `llama3`         | Highly capable ChatGPT-like responses |

> You can swap models just by changing the `ChatOllama(model="...")` line in `main.py`.

---

## 🧪 Sample Output

```json
{
  "company_name": "Acme Corp",
  "year": "2023",
  "revenue": 4000000,
  "cogs": 1000000,
  "gross_profit": 3000000,
  "net_income": 900000
}
```

And the summary:

> "Revenue grew by 33% YoY, driven by a reduction in COGS. Net income margins improved significantly."

---

## 🧰 Dev Tips

* 🔁 Test with multiple years of the same company for meaningful comparisons.
* 📈 You can expand with vector search, embedding memory, and chat agents.
* 💡 Want a frontend? Try React or Next.js with PDF upload + insights viewer.

---

## 📌 Future Improvements

* [ ] Frontend dashboard for upload + summary viewer
* [ ] Embed Chroma Vector DB for deeper RAG
* [ ] Add visual charts for YoY trends
* [ ] Industry-specific prompt fine-tuning
* [ ] Ingest Excel (XLSX) files

---

## 🧑‍💻 Built By

**MARYUM** — AI Engineer | Product Builder | Financial Tech Enthusiast
[LinkedIn](https://linkedin.com/in/maryum_urooj_ahmed) | [Twitter](https://twitter.com/mar_ooj)

---

## 📜 License

MIT License. Use it. Extend it. Build better AI tooling for finance 💸



