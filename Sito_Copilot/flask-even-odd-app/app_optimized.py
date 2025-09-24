"""
Optimized Flask Number Analyzer Application

Performance improvements:
- LRU caching for prime and factorial calculations
- Separated business logic from route handlers
- Optimized prime checking algorithm
- Improved error handling
"""

from flask import Flask, render_template, request
import math
from typing import List, Dict, Any
from functools import lru_cache

app = Flask(__name__)

# In-memory storage for history (max 10 entries)
history: List[Dict[str, Any]] = []

@lru_cache(maxsize=1000)
def is_prime(n: int) -> bool:
    """Optimized prime checker with caching and even number skip."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # Check odd divisors only
    for i in range(3, int(math.isqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

@lru_cache(maxsize=20)
def factorial(n: int) -> int | str:
    """Cached factorial computation with bounds checking."""
    if n < 0:
        raise ValueError("Negative numbers do not have a factorial.")
    if n >= 20:
        return "too large"
    return math.factorial(n)

def add_to_history(entry: Dict[str, Any]) -> None:
    """Add entry to history, maintaining max 10 items."""
    history.insert(0, entry)
    if len(history) > 10:
        history.pop()

def analyze_number(num: int) -> Dict[str, Any]:
    """Analyze number properties: even/odd, factorial, prime."""
    return {
        'number': num,
        'even_odd': "even" if num % 2 == 0 else "odd",
        'factorial': factorial(num),
        'prime': is_prime(num)
    }

@app.route('/', methods=['GET', 'POST'])
def home():
    """Main route handling form input and number analysis."""
    if request.method == 'POST':
        num_str = request.form.get('number', '').strip()
        try:
            num = int(num_str)
            result = analyze_number(num)
            add_to_history(result)
            return render_template('result.html', result=result)
        except ValueError:
            return render_template('index.html', error="Please enter a valid integer.")
    return render_template('index.html')

@app.route('/history')
def show_history():
    """Display history of analyzed numbers."""
    return render_template('history.html', history=history)

if __name__ == '__main__':
    # Run in debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5000)