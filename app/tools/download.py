import urllib3
import pdfplumber
import time
import io

def download_and_extract_text(url: str) -> str:
    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        headers = {
            'User-Agent': 'Mozilla/5.0',
        }

        for attempt in range(5):
            response = http.request("GET", url, headers=headers)
            if 200 <= response.status < 300:
                pdf_file = io.BytesIO(response.data)
                with pdfplumber.open(pdf_file) as pdf:
                    return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            elif attempt < 4:
                time.sleep(2 ** (attempt + 2))

        return "Failed to download PDF."

    except Exception as e:
        return f"Error downloading paper: {e}"
