document.getElementById('url-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const urlInput = document.getElementById('url-input').value.trim();
    if (!urlInput) {
        alert('Please enter a URL to classify.');
        return;
    }

    // Reset fields
    document.getElementById('overall-classification').textContent = 'Loading...';
    document.getElementById('overall-classification').className = 'badge';
    document.getElementById('domain-validity').textContent = 'Checking domain validity...';
    document.getElementById('good-percentage').textContent = 'Good: --%';
    document.getElementById('bad-percentage').textContent = 'Bad: --%';
    
    const embeddedUrlsContainer = document.getElementById('embedded-urls-row');
    embeddedUrlsContainer.innerHTML = '<p>Loading embedded URLs...</p>';
    embeddedUrlsContainer.classList.remove('show'); // Hide initially

    try {
        const response = await fetch('/classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: urlInput })
        });

        if (!response.ok) {
            throw new Error('Failed to classify URL');
        }

        const result = await response.json();

        // Update overall classification
        const overallClassification = result.overall_classification;
        const overallBadge = document.getElementById('overall-classification');
        overallBadge.textContent = overallClassification;
        overallBadge.className = `badge ${overallClassification.toLowerCase()}`;

        // If URL is Bad, alert the user
        if (overallClassification === 'Bad') {
            alert('⚠️ WARNING: This URL is classified as BAD. Avoid clicking on it.');
        }

        // Update domain validity and percentages
        document.getElementById('domain-validity').textContent = result.domain_validity;
        document.getElementById('good-percentage').textContent = `Good: ${result.percentages.good}`;
        document.getElementById('bad-percentage').textContent = `Bad: ${result.percentages.bad}`;

        // Update embedded URLs section
        embeddedUrlsContainer.innerHTML = ''; // Clear previous results

        if (result.embedded_urls.length > 0) {
            result.embedded_urls.forEach((urlObj) => {
                const url = urlObj.url;
                const classification = urlObj.classification;

                // Set character limit for truncation
                const charLimit = 50; 
                const shortenedUrl = url.length > charLimit ? url.substring(0, charLimit) + '...' : url;

                const urlCard = document.createElement('div');
                urlCard.className = 'embedded-url-card';
                urlCard.innerHTML = `
                    <p title="${url}">${shortenedUrl}</p>
                    <span class="badge ${classification.toLowerCase()}">${classification}</span>
                `;
                embeddedUrlsContainer.appendChild(urlCard);
            });
        } else {
            embeddedUrlsContainer.innerHTML = '<p>No embedded URLs found.</p>';
        }



        // Ensure the embedded URLs are displayed when the button is clicked
        document.getElementById('toggle-embedded-urls').addEventListener('click', function () {
            embeddedUrlsContainer.classList.toggle('show');
            this.textContent = embeddedUrlsContainer.classList.contains('show') ? 'Hide Embedded URLs' : 'Show Embedded URLs';
        });

    } catch (error) {
        alert('Error: ' + error.message);
    }
});
