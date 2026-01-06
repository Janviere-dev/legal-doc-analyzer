#  MINIJUST Legal Document Analyzer (AI Prototype)

This is a specialized **RAG (Retrieval-Augmented Generation)** application developed for the **Ministry of Justice**. It allows users to upload legal documents (PDF/Docx) and engage in a context-aware chat to extract insights and official legal citations.

##  Quick Start Instructions

Follow these steps to set up the environment and run the application on your local machine.

### 1. Prerequisites

* **Python 3.10+** installed on your system.
* A **Groq API Key** (provided via email/private message).

### 2. Installation & Setup

Open your terminal in the project folder and run the following commands:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the environment
# On Windows use: .venv\Scripts\activate
# On macOS/Linux use:
source .venv/bin/activate

# 3. Install required libraries
pip install -r requirements.txt

```

### 3. Environment Configuration

You must provide your API key for the AI to function:

1. Create a new file in the root folder named `.env`
2. Open the file and paste your key like this:
`GROQ_API_KEY=your_actual_key_here`

To get your **Groq API Key**, you just need to follow a few quick steps on their developer portal. It’s free and usually takes less than 60 seconds.

### 🔑 Step-by-Step Guide

1. **Visit the Console:** Go to [console.groq.com](https://console.groq.com).
2. **Sign Up / Login:** You can use your **Google account** or GitHub to sign in instantly.
3. **Navigate to Keys:** On the left-hand sidebar, click on the **"API Keys"** tab.
4. **Create Key:** Click the button that says **"Create API Key"**.
5. **Name It:** Give it a name like `MINIJUST_AI` so you remember what it's for.
6. **Copy & Save:** **Crucial!** Once the key appears, copy it immediately. Groq will never show it to you again for security reasons.


### 4. Running the Application

Launch the prototype by running:

```bash
streamlit run app.py

```

---

##  Troubleshooting

* **"Module Not Found"**: This usually means the Virtual Environment is not active. Run `source .venv/bin/activate` again.
* **"Externally Managed Environment"**: Ensure you have created and activated the `.venv` before running the `pip install` command.
* **Empty Responses**: Check your internet connection and verify that your API key in the `.env` file is correct and has not expired.
* **Processing Time**: Large PDF files may take a minute to "chunk" and index during the first upload.

---

**Vision 2026: A Year of Remarkable Change**

---

### 🚀 Next Step

Now that your files are ready, would you like me to help you draft the **body of the email** that contains the **API Key** and the link to the GitHub repo so it looks professional for your supervisor?
