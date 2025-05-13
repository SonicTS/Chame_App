# Chame_App
A Finanz project for the chargenmesse

## Project Overview

The **Chame_App** is a financial management application designed for the Chargenmesse. It provides a user-friendly interface for managing products, users, transactions, and toast rounds. The application is divided into a backend and frontend, with a database instance serving as the interface for data management.

### Backend
The backend is implemented in Python using Flask. It handles the business logic, database interactions, and API endpoints. Key components include:
- **`services`**: Contains the `admin_webpage.py` file, which defines the Flask routes and serves the frontend templates.
- **`models`**: Defines the database tables and their relationships using SQLAlchemy.
- **`chame_app`**: Includes the main application logic, configuration, and database instance.

### Frontend
The frontend is built using HTML, CSS, and JavaScript. It provides the user interface for interacting with the application. Key components include:
- **Templates**: Located in `frontend/admin_webpage/templates`, these define the structure of the web pages.
- **Static Files**: Located in `frontend/admin_webpage/static`, these include CSS for styling and JavaScript for interactivity.

### Database Instance
The database instance is implemented using SQLAlchemy. It provides an interface for interacting with the database, including querying, adding, and updating records. The database is initialized in `database_instance.py` and used throughout the backend.

### Database Tables
The application uses the following tables:
- **`User`**: Stores user information, including name, balance, and role.
- **`Product`**: Stores product details, such as name, category, price, and stock.
- **`Ingredient`**: Stores ingredient details, including name, price per unit, and stock quantity.
- **`ProductIngredient`**: Defines the relationship between products and their ingredients.
- **`Sale`**: Records sales transactions, including user, product, quantity, and total price.
- **`ToastRound`**: Links multiple sales to a single toast round.
- **`Bank`**: Tracks financial transactions.
- **`Transaction`**: Records individual financial transactions.

Each table is defined in the `models` directory and managed using SQLAlchemy ORM.

### How It Works
1. **Backend**: The backend serves the frontend templates and provides API endpoints for database operations.
2. **Frontend**: The frontend interacts with the backend via forms and AJAX requests.
3. **Database**: The database instance handles all data operations, ensuring a seamless connection between the backend and the database.

This architecture ensures a clear separation of concerns, making the application modular and easy to maintain.
