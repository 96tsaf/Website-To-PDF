# Website to PDF

Convert any website to PDF. Made this because I needed it and figured others might too.

## How it works

You throw in a URL, it spits out a PDF. Uses Selenium with Chrome to render the page like a real browser would, then saves it as PDF. Pretty straightforward.

## Setup

You'll need Python 3.11+ and Chrome browser installed. Then:

```bash
pip install -r requirements.txt
```

That's it. ChromeDriver gets downloaded automatically on first run.

## Running it

```bash
uvicorn main:app --reload
```

Server runs on `http://localhost:8000`

Check out `http://localhost:8000/static/index.html` for a basic test page, or hit up `/docs` to see the API endpoints.

## API Usage

POST to `/convert` with this:

```json
{
  "url": "https://whatever-site.com",
  "format": "A4",
  "landscape": false,
  "print_background": true
}
```

Only URL is required. Everything else is optional.

### curl example

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}' \
  --output website.pdf
```

### Python example

```python
import requests

r = requests.post(
    "http://localhost:8000/convert",
    json={"url": "https://example.com"}
)

open("output.pdf", "wb").write(r.content)
```

## Options

- `url` - the website (required)
- `format` - paper size, defaults to A4
- `landscape` - sideways if you want
- `print_background` - keeps colors and background images


## License

MIT

