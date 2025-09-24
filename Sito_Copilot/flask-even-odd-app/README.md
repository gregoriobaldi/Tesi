# Flask Even Odd App

This project is a simple Flask web application that allows users to input an integer and receive information about whether the number is even or odd, its factorial (if less than 20), and whether it is prime. The application also maintains a history of the last 10 inputs and their results.

## Project Structure

```
flask-even-odd-app
├── app.py                # Main entry point of the Flask application
├── templates             # Contains HTML templates
│   ├── base.html        # Base HTML structure with navbar
│   ├── home.html        # Form for inputting an integer and displaying results
│   └── history.html     # Displays the last 10 inputs and results
├── static               # Contains static files like CSS
│   └── style.css        # CSS styles for the application
├── requirements.txt     # Lists dependencies required for the project
└── README.md            # Documentation for the project
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd flask-even-odd-app
   ```

2. **Create a virtual environment** (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```
   python app.py
   ```

5. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:5000`.

## Usage

- On the homepage, you can input an integer into the form. After submitting, the application will display:
  - Whether the number is even or odd.
  - The factorial of the number (if less than 20, otherwise it will show "too large").
  - Whether the number is prime.

- The "History" page shows the last 10 inputs along with their results.

## Dependencies

- Flask

## License

This project is licensed under the MIT License.