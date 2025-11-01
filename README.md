# Over The Board (OTB)

<img width="640" height="320" alt="image" src="https://github.com/user-attachments/assets/382236f9-2469-4051-8c35-7075be475b3f" />

> **Your platform for finding and registering for live chess tournaments.**

---

## OTB - Overview

### What does it do?

OTB is a free and ad-free web platform that allows chess players to find and register for over-the-board tournaments. It centralizes tournaments in one place, providing a simple, clear, and accessible interface for both players and organizers.

### Why use it?

Because it focuses on what truly matters: Chess.
OTB removes unnecessary complexity, avoids clutter, and delivers a fast, functional, and modern experience for anyone who wants to play or organize tournaments without distractions.

### Who is it for?

OTB is for chess players, clubs, and organizers who want a practical way to share and participate in live chess events. Whether you’re a player looking for your next tournament or an organizer publishing your events, OTB is built for you.

---

## Tech Stack

OTB is built on a lightweight and efficient stack referred to as **SFJT**:

* **S**QLite – Simple, portable, and reliable local database
* **F**astAPI – Modern and fast Python web framework
* **J**inja2 – Clean and flexible HTML templating engine
* **T**abler – Responsive and batteries included front-end UI system

This stack keeps the project easy to maintain, fast to deploy, and friendly for contributors.

---

## Getting Started

To run OTB locally, follow these steps:

```bash
# 1. Clone the repository
git clone https://github.com/Emersh0w/Over-The-Board.git
cd Over-The-Board

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn main:app --reload
```

Once running, open your browser and go to **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

---

## Contributing

Contributing to OTB is simple.
Half of the project is written in Python, and the other half is HTML. You can choose the part you prefer and start improving the platform.

### To contribute:

* Create an Issue and give us feedback! It's that easy.
* Or you can solve one issue labeled **"Good First Issue"** in the repository.
* You can also add new pages, improve templates, or create new API routes.

OTB is open to contributions from developers, designers, and chess enthusiasts alike.

---

## Development

OTB is developed following **AGILE principles**, with short iterations, regular feedback, and continuous improvement.
The goal is to build something genuinely useful through incremental and community-driven updates, instead of large, infrequent releases.

---

## About the Creator

OTB is developed by a **chess player, arbiter, and tournament organizer** who, from the very beginning, felt the lack of a single, accessible tool to gather all tournaments in one place.
The project was created to make finding and joining live chess tournaments simple, free, and available to everyone.

---

## License

This project is licensed under the **AGPL-3.0 License**.
See the [LICENSE](./LICENSE) file for more details.
