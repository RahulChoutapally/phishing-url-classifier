from flask import Flask, request, render_template, jsonify
import whois
import re
import pickle
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load the trained model
loaded_model = pickle.load(open('htmlcontent.pkl', 'rb'))

# Function to classify a URL
def classify_url(url):
    try:
        prediction = loaded_model.predict([url])
        return "Good" if prediction[0] == "good" else "Bad"
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract URLs from a webpage
def extract_urls_from_html(base_url):
    if not re.match(r'^https?://', base_url):
        base_url = 'https://' + base_url  

    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        urls = []

        for a_tag in soup.find_all('a', href=True):
            extracted_url = a_tag['href']
            if not re.match(r'^https?://', extracted_url):
                extracted_url = urljoin(base_url, extracted_url)

            parsed_url = urlparse(extracted_url)
            if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc:
                urls.append(extracted_url)
        return urls
    except requests.exceptions.RequestException as e:
        return f"Error fetching {base_url}: {str(e)}"

# Function to check domain WHOIS data
def check_domain_whois(domain):
    try:
        domain_info = whois.whois(domain)
        if domain_info.domain_name:
            return f"Domain {domain} is valid and registered."
        else:
            return f"Domain {domain} is not registered or might be incorrect."
    except Exception as e:
        return f"Error checking domain WHOIS: {str(e)}"

def classify_url_and_embedded_urls(url):
    output = {
        "overall_classification": "",
        "domain_validity": "",
        "percentages": {"good": "--%", "bad": "--%"},
        "embedded_urls": []
    }

    # Check domain validity
    parsed_url = urlparse(url)
    output["domain_validity"] = check_domain_whois(parsed_url.netloc)

    # Classify the main URL
    main_url_result = classify_url(url)
    output["overall_classification"] = main_url_result

    # Extract and classify embedded URLs regardless of the main URL classification
    embedded_urls = extract_urls_from_html(url)
    
    if isinstance(embedded_urls, list):
        total_urls = len(embedded_urls)
        good_urls = 0
        bad_urls = 0

        for embedded_url in embedded_urls:
            embedded_result = classify_url(embedded_url)
            output["embedded_urls"].append({"url": embedded_url, "classification": embedded_result})

            if embedded_result == "Good":
                good_urls += 1
            elif embedded_result == "Bad":
                bad_urls += 1

        output["percentages"]["good"] = f"{(good_urls / total_urls) * 100:.2f}%" if total_urls else "--%"
        output["percentages"]["bad"] = f"{(bad_urls / total_urls) * 100:.2f}%" if total_urls else "--%"

    return output


# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = classify_url_and_embedded_urls(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
