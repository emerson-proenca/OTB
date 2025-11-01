# Over The Board 🏆

Welcome to **Over The Board (OTB)**!
A modern and robust **open-source API** to fetch chess tournament and player information from federations worldwide.

> **Note**: This is a community-driven project and has no official connection with any chess federation.

---

## 🚀 Features

### ✅ Available


* **Smart caching** – Faster performance with in-memory cache
* **Rate limiting** – Protection against abuse and overload
* **Advanced logging** – Structured logs for debugging
* **CORS enabled** – Access API from any origin
* **Auto-generated documentation** – Swagger UI and ReDoc

### 🔄 In Development

- **FIDE Tournaments** – International tournaments
- **USCF Integration** – United States Chess Federation
- **Chess-results.com** – Largest tournament database worldwide

---

## 📋 Endpoints

| Endpoint         | Method | Description                      |
| ---------------- | ------ | -------------------------------- |
| `/`              | GET    | API information                  |
| `/health`        | GET    | Application health status        |

| `/cache/stats`   | GET    | Cache statistics                 |
| `/cache/clear`   | DELETE | Clear cache                      |
| `/docs`          | GET    | Swagger documentation            |
| `/redoc`         | GET    | ReDoc documentation              |

---

## 🛠️ Tech Stack

- **FastAPI** – Modern Python web framework
- **Python 3.8+** – Main programming language
- **BeautifulSoup4** – Web scraping utilities
- **Uvicorn** – ASGI server
- **Requests** – HTTP client
- **Jinja2** – Template engine

---

## 🏃‍♂️ How to Run

### Requirements

- Python 3.8+
- pip (package manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd otb-api
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create the Database**

   ```bash
   python -m database.migration
   ```

4. **Run the API**

   ```bash
   python main.py
   ```

   Or run directly with Uvicorn:

   ```bash
   python -m uvicorn main:app --reload
   ```

### 🌐 Access

Once running, the API will be available at:

- **API**: [https://over-the-board.onrender.com](https://over-the-board.onrender.com)
- **Swagger Docs**: [https://over-the-board.onrender.com/docs](https://over-the-board.onrender.com/docs)
- **ReDoc**: [https://over-the-board.onrender.com/redoc](https://over-the-board.onrender.com/redoc)

---

## 📖 Usage Examples

### Fetch tournaments from 2025



### Fetch players from São Paulo

```bash
curl "https://over-the-board.onrender.com/players?state=SP&pages=1"
```


---

## ⚙️ Configuration

The API supports configuration via environment variables:

- `DEBUG` – Debug mode (true/false)
- `RATE_LIMIT_REQUESTS` – Requests per minute limit
- `CACHE_TTL_DEFAULT` – Default cache TTL in seconds
- `HTTP_TIMEOUT` – HTTP request timeout
- `LOG_LEVEL` – Logging level (DEBUG, INFO, WARNING, ERROR)

---

## 📊 Advanced Features

### Cache

- In-memory cache
- Configurable TTL per endpoint
- Monitoring endpoint: `/cache/stats`

### Rate Limiting

- Default: 100 requests/minute per IP (configurable)
- Informative headers: `X-RateLimit-*`
- Returns `429` when exceeded

### Logging

- Structured logs
- Log file: `otb_api.log`
- Verbosity levels configurable

---

## 🏗️ Future Architecture

```
over-the-board/
├── apis/
│   ├── players_api.py
│   ├── tournaments_api.py

├── core/
│   ├── cache.py
│   ├── schemas.py
│   └── utils.py
├── db/
│   ├── models.py
│   ├── session.py
│   └── migration.py
├── static/
│   ├── css/
│   │   └── css/styles.css
│   ├── js/
│   │   └── scripts.js
│   ├── locales/
│   │   ├── en-us.json
│   │   ├── pt-br.json
│   │   └── translation-guide.md
│   └── index.html
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── main.py
```

---

## 🤝 Contributing

Contributions are welcome!
The goal is to make **OTB the world’s most comprehensive chess tournament API**.

### Steps:

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **AGPL-3.0 license**. See the [LICENSE](LICENSE) file for details.

---

## 🚧 Project Status

**Current version**: 0.8.1
**Progress**: \~15% complete
**Next milestone**: FIDE integration

---

Made ❤️ for the chess community!
