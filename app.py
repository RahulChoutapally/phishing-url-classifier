from flask import Flask, request, render_template, jsonify
import whois
import re
import pickle
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Load the pre-trained logistic regression model
loaded_model = pickle.load(open('htmlcontent.pkl', 'rb'))

# Function to classify URL using the loaded model
def classify_url(url):
    try:
        prediction = loaded_model.predict([url])
        return "Good" if prediction[0] == "good" else "Bad"
    except Exception as e:
        return f"Error: {str(e)}"

# Function to extract and clean embedded URLs from the HTML content of a URL
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

# Function to check domain validity using WHOIS
def check_domain_whois(domain):
    try:
        domain_info = whois.whois(domain)
        if domain_info.domain_name:
            return f"Domain {domain} is valid and registered."
        else:
            return f"Domain {domain} is not registered or might be incorrect."
    except Exception as e:
        return f"Error checking domain WHOIS: {str(e)}"

# Function to classify the main URL and its embedded URLs
def classify_url_and_embedded_urls(url):
    output = {}
    main_url_result = classify_url(url)
    good_urls = 0
    bad_urls = 0

    if not re.match(r'^https?://', url):
        url = 'https://' + url

    domain = urlparse(url).netloc
    domain_validity = check_domain_whois(domain)
    output["Domain Validity"] = domain_validity

    embedded_urls = extract_urls_from_html(url)
    if isinstance(embedded_urls, list):  
        total_urls = len(embedded_urls)
        for embedded_url in embedded_urls:
            embedded_result = classify_url(embedded_url)
            output[embedded_url] = embedded_result
            if embedded_result == "Good":
                good_urls += 1
            elif embedded_result == "Bad":
                bad_urls += 1
        output["Good URLs Percentage"] = f"{(good_urls / total_urls) * 100:.2f}%"
        output["Bad URLs Percentage"] = f"{(bad_urls / total_urls) * 100:.2f}%"
    else:
        output["Embedded URL extraction error"] = embedded_urls
        output["Good URLs Percentage"] = "0%"
        output["Bad URLs Percentage"] = "0%"

    return output

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    url = data.get('url')
    if url:
        classification_data = classify_url_and_embedded_urls(url)

        # Calculate overall classification
        main_url_classification = classify_url(url)
        good_percentage = float(classification_data.get("Good URLs Percentage", "0%").replace("%", ""))
        overall_classification = "Good" if main_url_classification == "Good" and good_percentage > 80 else "Bad"

        # Organize the response into sections
        response = {
            "overall_classification": overall_classification,
            "embedded_urls": [],
            "domain_validity": classification_data.get("Domain Validity", "Unknown"),
            "percentages": {
                "good": classification_data.get("Good URLs Percentage", "0%"),
                "bad": classification_data.get("Bad URLs Percentage", "0%"),
            }
        }

        # Extract and organize embedded URLs
        for key, value in classification_data.items():
            if key not in ["Domain Validity", "Good URLs Percentage", "Bad URLs Percentage", "No embedded URLs found", "Embedded URL extraction error"]:
                response["embedded_urls"].append({"url": key, "classification": value})

        return jsonify(response)
    return jsonify({'error': 'No URL provided'}), 400


if __name__ == "__main__":
    app.run(debug=True)
