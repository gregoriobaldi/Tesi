"""
Flask Number Analyzer Application

Features:
- Homepage with a form to input an integer.
- On submit: shows if it’s even/odd, its factorial (if <20, otherwise “too large”), and if it’s prime.
- /history page shows the last 10 inputs with results (stored in-memory).
- Navbar links "Home" and "History".
"""

from flask import Flask, render_template, request, redirect, url_for
import math
from typing import List, Dict, Any

app = Flask(__name__)

# In-memory storage for history (list of dicts)
history: List[Dict[str, Any]] = []

def is_prime(n: int) -> bool:
    """
    Check if a number is prime.
    Returns True if n is prime, False otherwise.
    """
    if n < 2:
        return False
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def factorial(n: int) -> int | str:
    """
    Compute factorial of n if n < 20, else return 'too large'.
    Raises ValueError for negative inputs.
    """
    if n < 0:
        raise ValueError("Negative numbers do not have a factorial.")
    if n >= 20:
        return "too large"
    return math.factorial(n)

def add_to_history(entry: Dict[str, Any]) -> None:
    """
    Add a result entry to the history, keeping only the last 10.
    """
    history.insert(0, entry)
    if len(history) > 10:
        history.pop()

@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Homepage: form for integer input and result display.
    """
    error = None
    result = None
    if request.method == 'POST':
        num_str = request.form.get('number', '').strip()
        try:
            num = int(num_str)
            even_odd = "even" if num % 2 == 0 else "odd"
            fact = factorial(num)
            prime = is_prime(num)
            result = {
                'number': num,
                'even_odd': even_odd,
                'factorial': fact,
                'prime': prime
            }
            add_to_history(result)
            return render_template('result.html', result=result)
        except ValueError:
            error = "Please enter a valid integer."
    return render_template('index.html', error=error)

@app.route('/history')
def show_history():
    """
    History page: shows the last 10 inputs and their results.
    """
    return render_template('history.html', history=history)

if __name__ == '__main__':
    app.run(debug=True)