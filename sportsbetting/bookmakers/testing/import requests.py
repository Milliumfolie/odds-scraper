import requests

headers = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )
}

r = requests.get(
    "https://www.oddsportal.com/football/netherlands/eredivisie/",
    headers=headers,
    timeout=15,
    verify=r"C:\certs\_.oddsportal.crt",
)
print(r.status_code)