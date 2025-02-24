from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from utils.scraper import scrape_website
from utils.validator import validate_csv
from flask_sock import Sock
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
sock = Sock(app)
app.config["UPLOAD_FOLDER"] = "uploads"

# Create uploads directory if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/")
def index():
    """Render the main upload page"""
    return render_template("index.html")

@sock.route('/ws')
def websocket(ws):
    """Handle WebSocket connections and scraping process"""
    try:
        print("New WebSocket connection established")
        while True:
            try:
                # Receive data from WebSocket
                data = ws.receive()
                if not data:
                    continue

                data = json.loads(data)
                print(f"Received data: {data}")  # Debug log

                if data.get('type') == 'start_scrape':
                    urls = data.get('urls', [])
                    total_urls = len(urls)
                    results = []
                    print(f"Starting scrape of {total_urls} URLs")

                    # Process each URL
                    for i, url in enumerate(urls, 1):
                        print(f"Scraping site {i}/{total_urls}: {url}")
                        try:
                            # Define callback for progress updates
                            def progress_callback(result):
                                ws.send(json.dumps({
                                    'type': 'progress',
                                    'current': i,
                                    'total': total_urls,
                                    'pages': result.get('pages_scraped', 0)
                                }))

                            # Scrape website
                            result = scrape_website(
                                url,
                                callback=progress_callback,
                                max_pages=10  # Adjust max pages to scrape
                            )
                            results.append(result)

                            # Send result
                            ws.send(json.dumps({
                                'type': 'result',
                                'result': result
                            }))

                        except Exception as e:
                            print(f"Error scraping {url}: {str(e)}")
                            # Send error for this specific URL
                            ws.send(json.dumps({
                                'type': 'error',
                                'message': f"Error scraping {url}: {str(e)}"
                            }))
                            continue

                    # Save results to CSV
                    try:
                        output_file = "scraped_data.csv"
                        output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_file)
                        df = pd.DataFrame(results)
                        df.to_csv(output_path, index=False)

                        # Send completion message
                        ws.send(json.dumps({
                            'type': 'complete',
                            'filename': output_file
                        }))
                        print("Scraping completed successfully")
                    except Exception as e:
                        print(f"Error saving results: {str(e)}")
                        ws.send(json.dumps({
                            'type': 'error',
                            'message': f"Error saving results: {str(e)}"
                        }))

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': f"Invalid JSON: {str(e)}"
                }))
            except Exception as e:
                print(f"WebSocket error: {str(e)}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': f"Error: {str(e)}"
                }))

    except Exception as e:
        print(f"Fatal WebSocket error: {str(e)}")
        try:
            ws.send(json.dumps({
                'type': 'error',
                'message': f"Fatal error: {str(e)}"
            }))
        except:
            pass

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and validate CSV"""
    try:
        if "file" not in request.files:
            return "No file part", 400

        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400

        # Validate CSV file
        if not validate_csv(file):
            return "Invalid CSV file", 400

        # Read URLs from CSV
        urls = pd.read_csv(file)["Website"].tolist()
        total = len(urls)
        print(f"Processing {total} URLs")  # Debug log

        # Render template with URLs
        return render_template("results.html", total=total, urls=urls)
    except Exception as e:
        print(f"Upload error: {str(e)}")  # Debug log
        return f"Error processing file: {str(e)}", 400

@app.route("/download/<filename>")
def download_file(filename):
    """Handle file download"""
    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(file_path):
            return "File not found", 404
        return send_file(
            file_path,
            as_attachment=True,
            download_name="scraped_results.csv"
        )
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500

@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    from datetime import datetime
    return {
        "current_year": datetime.utcnow().year  # Return the year value directly
    }

if __name__ == "__main__":
    app.run(debug=True)
