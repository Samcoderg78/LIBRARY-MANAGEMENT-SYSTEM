# Library Management System

A Flask web application for managing and reading e-books, similar to an online e-book store. It has two sides: an **Admin** side for managing the catalogue and a **User** side for finding and reading books.

**Course project:** Modern Application Development I (MAD-1), IIT Madras BS in Data Science & Applications

**Demo video:** [Watch on Google Drive](https://drive.google.com/file/d/16pJNqIOL-QvS219imKpoIdNuQDVrl1D2/view?usp=drive_link)

---

## Features

### Admin
- Create, update and delete book **sections** (categories)
- Create, update and delete **books**
- Keep the catalogue up to date as students' requirements change

### User
- **Search** for books
- **Request** a book
- **Read** a book online
- **Download** a book

---

## Tech stack

| Technology | Used for |
|---|---|
| Python | Programming language |
| Flask | Web framework |
| Jinja2 | HTML templating |
| HTML + Bootstrap | Frontend pages and styling |
| SQLAlchemy / Flask-SQLAlchemy | Database models and queries |
| Werkzeug | Utilities used by Flask |

---

## Project structure

```
MAD-1-Project/
├── 23f1003171Report.pdf     # Project report
└── CODE/
    ├── static/              # CSS, images and other static files
    ├── templates/           # Jinja2 HTML templates
    └── app.py               # Flask application
```

---

## Getting started

### Prerequisites
- Python 3.8 or higher

### Installation
```bash
git clone 
cd MAD-1-Project/CODE
pip install flask flask-sqlalchemy matplotlib
```

### Run the app
```bash
python app.py
```
Then open `http://127.0.0.1:5000` in your browser.

---

## Documentation

- **Project report:** `23f1003171Report.pdf`
- **Demo video:** see the link at the top

---

## Author

**Saurabh Yadav**: [GitHub](https://github.com/Samcoderg78) · [LinkedIn](https://linkedin.com/in/saurabh-yadav-6zd)
