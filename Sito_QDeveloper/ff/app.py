from flask import Flask, render_template, request, redirect, url_for, session
from math import factorial, isqrt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session usage

# Helper functions
def is_even(n: int) -> bool:
    """Return True if n is even, False otherwise."""
    return n % 2 == 0

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, isqrt(n) + 1):
        if n % i == 0:
            return False
    return True

def get_factorial(n: int):
    """Return factorial if n < 20, else return None."""
    if n < 0:
        return None
    if n < 20:
        return factorial(n)
    return None

def add_to_history(entry: dict):
    """Add a result entry to session-based history (max 10 items)."""
    history = session.get('history', [])
    history.insert(0, entry)
    session['history'] = history[:10]

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Homepage: Accepts integer input, computes properties, and shows result.
    """
    if request.method == 'POST':
        try:
            num = int(request.form['number'])
        except (ValueError, KeyError):
            return render_template('index.html', error="Please enter a valid integer.")

        even = is_even(num)
        prime = is_prime(num)
        fact = get_factorial(num)
        fact_display = fact if fact is not None else "too large"

        result = {
            'number': num,
            'even': even,
            'prime': prime,
            'factorial': fact_display
        }
        add_to_history(result)
        return render_template('result.html', result=result)
    return render_template('index.html')

@app.route('/history')
def history():
    """
    Show the last 10 inputs and their results.
    """
    history = session.get('history', [])
    return render_template('history.html', history=history)

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)