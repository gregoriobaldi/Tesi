# Flask Number Analyzer

A simple Flask web app to analyze integers:
- Check if even/odd
- Compute factorial (if <20)
- Check if prime
- Show last 10 inputs/results (in-memory)

## Usage

```bash
pip install -r requirements.txt
python app.py
```

Visit [http://localhost:5000](http://localhost:5000)

## Structure

- `app.py`: Main Flask app with routes and logic
- `templates/`: HTML templates
- `static/`: CSS
- `requirements.txt`: Dependencies

## Notes

- History is stored in user session (in-memory, per browser).