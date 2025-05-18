from flask import Flask, render_template, request, redirect, url_for, session, abort, send_from_directory,  jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_


import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os



app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER1'] = 'static/images'  # Define upload folder for storing image files
app.config['UPLOAD_FOLDER2'] = 'static/books'   # Define upload folder for storing book files
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(10))
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Date created field
    image = db.Column(db.String(255), nullable=False)
    book = db.relationship('Book', backref='section', lazy=True)  


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    book_file = db.Column(db.String(255), nullable=False)  # New attribute for storing the uploaded book file
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    returned = db.Column(db.Boolean, default=False)  # New field for book return status
    return_date = db.Column(db.DateTime)  # New field for book return date
    
class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    date_issued = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=False)
    # Define a relationship to the User model
    user = db.relationship('User', backref='book_requests')
    book = db.relationship('Book', backref='book_requests')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    rating = db.Column(db.Integer)  # Optional rating
    comment = db.Column(db.Text)
    date_given = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
     # Define relationship to the Book model
    book = db.relationship('Book', backref='feedbacks')




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    name = request.form['name']
    role = request.form['role']

    if role == 'user':
        new_user = User(username=username, email=email, name=name, password=password)
        db.session.add(new_user)
        flash('User registered successfully')
    elif role == 'librarian':
        new_librarian = Librarian(username=username, email=email, password=password)
        db.session.add(new_librarian)
        flash('Librarian registered successfully')
    
    try:
        db.session.commit()
        return redirect('/login')
    except IntegrityError:
        return "Username or email already exists!"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':    
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role == 'user':
            user = User.query.filter_by(email=email, password=password).first()
            if user:
                session['username'] = user.username
                session['user_id'] = user.id  # Store user ID in the session
                return redirect('/user_dashboard')
        elif role == 'librarian':
            librarian = Librarian.query.filter_by(email=email, password=password).first()
            if librarian:
                session['username'] = librarian.username
                return redirect('/librarian_dashboard')

        return 'Please enter correct credentials!'
    return render_template('index.html') 


@app.route('/librarian_dashboard')
def librarian_dashboard():
    if 'username' in session:
        sections = Section.query.all()  # Fetch all sections from the database
        books = Book.query.all()  # Fetch all books from the database
        pending_requests = BookRequest.query.filter_by(approved=False).all()
        books_requested = [(request, Book.query.get(request.book_id),request.user_id) for request in pending_requests]
        return render_template('librarian_dashboard.html',sections=sections, books=books, books_requested=books_requested) # Pass sections, books and requests to the template
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/add_section', methods=['GET','POST'])
def add_section():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        image = request.files['image']

        # Save the uploaded image
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER1'], image_filename))

        # Create a new Section object
        new_section = Section(title=title, description=description,  image=image_filename)

        # Add the new section to the database session
        db.session.add(new_section)

        # Commit the changes to the database
        db.session.commit()

        # Redirect to the librarian dashboard
        return redirect(url_for('librarian_dashboard'))
    
# 1. Route for deleting a section
@app.route('/delete_section/<int:section_id>', methods=['POST'])
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()
    return redirect(url_for('librarian_dashboard'))    


@app.route('/librarian_dashboard/<int:section_id>')
def display_section_books(section_id):
    section = Section.query.get(section_id)
    if section:
        books = Book.query.filter_by(section_id=section_id).all()
        return render_template('add_book.html', sections=[section], books=books)
    else:
        abort(404)  # Section not found, return a 404 error


    
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        author = request.form['author']
        description = request.form['description']
        image = request.files['image']
        price = request.form['price']
        book_file = request.files['book']
        section_id = request.form['section']

        # Save the uploaded image
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER1'], image_filename))
        book_filename = secure_filename(book_file.filename)
        book_file.save(os.path.join(app.config['UPLOAD_FOLDER2'], book_filename))

        # Create a new Book object
        new_book = Book(title=title, author=author, description=description, image=image_filename,price=price, book_file=book_filename,  section_id=section_id)

        # Add the new book to the database session
        db.session.add(new_book)

        # Commit the changes to the database
        db.session.commit()
        
        # Redirect to the librarian dashboard
        return redirect(url_for('librarian_dashboard'))
    
@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    # Query the book to be deleted
    book = Book.query.get_or_404(book_id)

    try:
        # Delete the book from the database
        db.session.delete(book)
        db.session.commit()
        return redirect('/librarian_dashboard')  # Redirect to the librarian dashboard after deletion
    except Exception as e:
        return f"An error occurred: {str(e)}"  # Handle errors gracefully
    

@app.route('/user_dashboard')
def user_dashboard():
    if 'username' in session and 'user_id' in session:
        user = User.query.get(session['user_id'])
        books = Book.query.all()
        
        my_books = db.session.query(Book, BookRequest.date_issued, BookRequest.return_date) \
            .join(BookRequest, BookRequest.book_id == Book.id) \
            .filter(BookRequest.user_id == user.id, BookRequest.approved == True, Book.returned==False) \
            .all()
        return render_template('user_dashboard.html', user=user,books=books, my_books=my_books)
    else:
        # Handle the case where the user is not logged in
        return redirect(url_for('login'))


@app.route('/request_book', methods=['POST'])
def request_book():
    if 'username' in session:
        user_id = session['user_id']
        book_ids = request.form.getlist('book_id')  # Assuming you are sending a list of book IDs
        
        # Create book request entries for each selected book
        for book_id in book_ids:
            # Check if the user already has this book
            existing_request = BookRequest.query.filter_by(user_id=user_id, book_id=book_id).first()
            if existing_request:
                return "You have already requested one or more of these books."
            
            book = Book.query.get(book_id)
            if book.returned:  # If book has been returned, update status and re-request
                book.returned = False
                db.session.commit()

            return_date = datetime.utcnow() + timedelta(days=1)
            book_request = BookRequest(user_id=user_id, book_id=book_id, return_date=return_date)
            db.session.add(book_request)
        
        db.session.commit()
        
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/approve_request/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    if 'username' not in session:  # Ensure the user is logged in
        return redirect(url_for('login'))
    
    book_request = BookRequest.query.get(request_id)
    book_request.approved = True
    
    db.session.commit()
    return redirect(url_for('librarian_dashboard'))

@app.route('/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    if 'username' not in session:  # Ensure the user is logged in
        return redirect(url_for('login'))
    
    book_request = BookRequest.query.get(request_id)
    db.session.delete(book_request)  # Delete the request from the database
    db.session.commit()
    return redirect(url_for('librarian_dashboard'))
    
# Route for serving books to users
@app.route('/serve_book/<int:book_id>')
def serve_book(book_id):
    if 'username' in session and 'user_id' in session:
        user_id = session['user_id']
        
        # Check if the book request exists and is approved
        book_request = BookRequest.query.filter_by(book_id=book_id, user_id=user_id, approved=True).first()
        if book_request:
            # Fetch the requested book
            book = Book.query.get(book_id)
            if book:
                # Serve the book file
                return send_from_directory(app.config['UPLOAD_FOLDER2'], book.book_file)
            else:
                flash('Book not found', 'danger')
                return redirect(url_for('user_dashboard'))  # Redirect if book not found
        else:
            flash('You are not authorized to access this book', 'danger')
            return redirect(url_for('user_dashboard'))  # Redirect if not authorized
    else:
        flash('Please login to access the book', 'danger')
        return redirect(url_for('login'))  # Redirect if not logged in
    
    

# Add this route to fetch user information for a given book
@app.route('/get_issued_info/<int:book_id>')
def get_issued_info(book_id):
    issued_info = []

    # Query the book requests for the given book
    book_requests = BookRequest.query.filter_by(book_id=book_id, approved=True).all()

    # Iterate over each book request to fetch user information
    for request in book_requests:
        user = User.query.get(request.user_id)
        issued_info.append({
            'user_id': user.id,
            'username': user.username,
            'issued_date': request.date_issued.strftime("%Y-%m-%d"),
            'return_date': request.return_date.strftime("%Y-%m-%d")
        })

    return jsonify(issued_info)    


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'POST':
        book = Book.query.get_or_404(book_id)
        book.title = request.form['title']
        book.author = request.form['author']
        book.description = request.form['description']
        book.price = request.form['price']
        section_id = request.form['section']
        book.section_id = section_id
        db.session.commit()
        return redirect(url_for('librarian_dashboard'))
    else:
        book = Book.query.get_or_404(book_id)
        sections = Section.query.all()
        return render_template('edit_book.html', book=book, sections=sections)

@app.route('/edit_section/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    if request.method == 'POST':
        section = Section.query.get_or_404(section_id)
        section.title = request.form['title']
        section.description = request.form['description']
        db.session.commit()
        return redirect(url_for('librarian_dashboard'))
    else:
        section = Section.query.get_or_404(section_id)
        return render_template('edit_section.html', section=section)

@app.route('/revoke_access/<int:book_id>', methods=['GET', 'POST'])
def revoke_access(book_id):
    # Query the book to revoke access
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        # Get the username from the form
        username = request.form['username']

        # Query the user by username
        user = User.query.filter_by(username=username).first()

        if user:
            try:
                # Revoke access for the specified user to the book
                book_request = BookRequest.query.filter_by(user_id=user.id, book_id=book.id).first()
                if book_request:
                    db.session.delete(book_request)
                    db.session.commit()
                    return redirect(url_for('librarian_dashboard'))  # Redirect to the librarian dashboard after revoking access
                else:
                    return "No access found for this user to the specified book."
            except Exception as e:
                return f"An error occurred: {str(e)}"  # Handle errors gracefully
        else:
            return "User not found."

    return render_template('revoke_access.html', book=book)

@app.route('/books/<int:book_id>')
def check_book(book_id):
    # Check if the book request exists and if it's overdue
    book_request = BookRequest.query.filter_by(book_id=book_id, user_id=session.get('user_id')).first()
    if book_request:
        if book_request.return_date < datetime.utcnow():
            book_request.approved = False
            db.session.commit()
            return "Access to this book has been revoked due to overdue return date."
        else:
            # Book is not overdue, serve the book file
            book = Book.query.get_or_404(book_id)
            return send_from_directory(app.config['UPLOAD_FOLDER2'], book.book_file)
    else:
        # Book request does not exist, handle accordingly (e.g., display an error message)
        return "You do not have access to this book."



@app.route('/return_book/<int:book_id>')
def return_book(book_id):
    if request.method == 'GET':
        book = Book.query.get(book_id)
        if book:           
            try:
                # Update book status
                book.returned = True
                book.return_date = datetime.now()
                # Delete existing BookRequest entry for this book
                existing_request = BookRequest.query.filter_by(book_id=book_id, approved=True).first()
                if existing_request:
                    db.session.delete(existing_request)
                # Commit changes to the database
                db.session.commit()
                flash('Book returned successfully', 'success')
                return redirect(url_for('user_dashboard'))
            except Exception as e:
                print("e")
                flash(f'Error returning book: {str(e)}', 'danger')
                return redirect(url_for('user_dashboard'))
        else:
            flash('Book not found', 'danger')
            return redirect(url_for('user_dashboard'))
    else:
        abort(405)  # Method not allowed


@app.route('/submit_feedback/<int:book_id>', methods=['GET'])
def show_feedback_form(book_id):
    if 'username' in session:
        return render_template('feedback_form.html', book_id=book_id)
    else:
        return redirect(url_for('login'))



@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'username' in session:
        user_id = session['user_id']
        book_id = request.form['book_id']
        rating = request.form.get('rating')
        comment = request.form['comment']

        # Create a new feedback entry
        new_feedback = Feedback(user_id=user_id, book_id=book_id, rating=rating, comment=comment)
        db.session.add(new_feedback)
        db.session.commit()

        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('user_dashboard'))
    else:
        return redirect(url_for('login'))


@app.route('/reviews/<int:book_id>')
def show_reviews(book_id):

    book = Book.query.get_or_404(book_id)
    reviews = Feedback.query.filter_by(book_id=book_id).all()
    return render_template('reviews.html', book=book, reviews=reviews)

@app.route('/search', methods=['GET'])
def search_books():
    query = request.args.get('query', '')
    # Perform the search based on the query
    books = Book.query.join(Section).filter(
        or_(
            Book.title.ilike(f'%{query}%'),
            Book.author.ilike(f'%{query}%'),
            Section.title.ilike(f'%{query}%')  # Search by section title
        )
    ).all()
    # Then render the template with the search results
    return render_template('search_results.html', books=books)

@app.route('/stats_admin')
def admin_stats():
    # Query data for the graphs
    feedbacks = Feedback.query.filter(Feedback.rating.isnot(None)).all()
    book_requests = BookRequest.query.filter_by(approved=True).all()
    sections = Section.query.all()

    # Extract book titles and ratings
    book_titles = [feedback.book.title for feedback in feedbacks]
    ratings = [feedback.rating for feedback in feedbacks]

    # Create the ratings plot
    fig, axes = plt.subplots(3, 1, figsize=(12, 18))

    # Plot ratings as a bar chart
    axes[0].barh(book_titles, ratings, color='blue', alpha=0.7)
    axes[0].set_xlabel('Rating')
    axes[0].set_ylabel('Book Title')
    axes[0].set_title('Book Ratings')

    # Extract book titles and count the number of users who have read each book
    book_titles_count = {}
    for request in book_requests:
        if request.book.title in book_titles_count:
            book_titles_count[request.book.title] += 1
        else:
            book_titles_count[request.book.title] = 1

    # Create the books read by users plot
    axes[1].barh(list(book_titles_count.keys()), list(book_titles_count.values()), color='green')
    axes[1].set_xlabel('Number of Users')
    axes[1].set_ylabel('Book Title')
    axes[1].set_title('Number of Users who Read Each Book')

    # Query data for the number of books available per section
    books_per_section = {section.title: len(section.book) for section in sections}

    # Create the pie graph for books available per section
    axes[2].pie(books_per_section.values(), labels=books_per_section.keys(), autopct='%1.1f%%', startangle=140)
    axes[2].set_title('Books Available per Section')

    # Save the plot to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode()

    # Render the stats page with the plots
    return render_template('stats_admin.html', plot_data=plot_data)

@app.route('/stats_user')
def stats_user():
    # Query data for the graphs
    user_id = 1  # Assuming user ID for demonstration
    books_read = BookRequest.query.filter_by(user_id=user_id, approved=True).all()
    sections = Section.query.all()

    # Extract book titles read by the user
    book_titles = [book_request.book.title for book_request in books_read]

    # Extract section titles and count the number of books in each section
    section_titles = [section.title for section in sections]
    books_per_section = {section.title: len(section.book) for section in sections}

    # Create the bar graph for books read by the user
    plt.figure(figsize=(8, 6))
    plt.barh(np.arange(len(book_titles)), [1]*len(book_titles), color='blue', alpha=0.7)
    plt.xlabel('Number of Books')
    plt.yticks(np.arange(len(book_titles)), book_titles)
    plt.title('Books Read by User')

    # Save the bar graph to a BytesIO object
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png')
    buffer1.seek(0)
    plot_data1 = base64.b64encode(buffer1.getvalue()).decode()

    # Create the pie graph for section distribution
    plt.figure(figsize=(8, 6))
    plt.pie(books_per_section.values(), labels=books_per_section.keys(), autopct='%1.1f%%', startangle=140)
    plt.title('Section Distribution')

    # Save the pie graph to a BytesIO object
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png')
    buffer2.seek(0)
    plot_data2 = base64.b64encode(buffer2.getvalue()).decode()

    # Render the template with the plots
    return render_template('stats_user.html', plot_data1=plot_data1, plot_data2=plot_data2)





# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
