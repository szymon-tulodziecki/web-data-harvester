import requests 
from bs4 import BeautifulSoup
import re
import asyncio
import aiohttp
import time

url = "https://ans-elblag.pl/"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup.title.text)

class ProfilDanych:
    @staticmethod
    def pobierz_email(soup):
        """Pobiera adres e-mail z profilu danych."""
        text = soup.get_text()
        emaile = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return list(set(emaile)) # lista emaili bez duplikatów
    
    @staticmethod
    def pobierz_adresy(soup):
        """Pobiera adresy z profilu danych."""
        text = soup.get_text()
        adresy = re.findall(r'\d{2}-\d{3}\s+[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż\s]+', text)
        return adresy[:5] #Test dla 5 adresów
    
    @staticmethod
    def pobierz_telefony(soup):
        """Pobiera numery telefonów z profilu danych."""
        text = soup.get_text()
        telefony = re.findall(r'(?:\+48\s?)?(?:\d{3}[-\s]?\d{3}[-\s]?\d{3}|\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})', text)
        return list(set(telefony))
    
    @staticmethod
    def pobierz_informacje(soup):
        """Pobiera dodatkowe informacje o organizacji."""
        org_info = []

        naglowki = soup.find_all(['h1', 'h2', 'h3'])

        for naglowek in naglowki[:3]: # Test dla 3 nagłówków
            if naglowek.get_text().strip():
                org_info.append(naglowek.get_text().strip()) 

        slowa_kluczowe = ['o-nas', 'o nas', 'nasza historia', 'kim jesteśmy', 'firma', 'organizacja', 'about', 'about-us', 'company']
        linki = soup.find_all('a', href=True)

        for link in linki:
            href = link['href'].lower()
            text = link.get_text().lower()
            if any(slowo_kluczowe in href or slowo_kluczowe in text for slowo_kluczowe in slowa_kluczowe):  # Poprawka: slowo_kluczowe zamiast slowa_kluczowe
                org_info.append(f"{link.get_text().strip()}: {link['href']}")
                if len(org_info) >= 5:  # Test dla 5 informacji
                    break
        
        return org_info
    
    @staticmethod
    async def pobierz_dane_async(session, url):
        """Asynchronicznie pobiera i przetwarza dane ze strony."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    dane = {
                        'url': url,
                        'tytul': soup.title.string if soup.title else 'Brak tytułu',
                        'emaile': ProfilDanych.pobierz_email(soup),
                        'adresy': ProfilDanych.pobierz_adresy(soup),
                        'telefony': ProfilDanych.pobierz_telefony(soup),
                        'informacje': ProfilDanych.pobierz_informacje(soup),
                        'czas_pobrania': time.time()
                    }
                    
                    print(f"✓ Pobrano dane z: {url}")
                    return dane
                else:
                    print(f"✗ Błąd HTTP {response.status}: {url}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"✗ Timeout: {url}")
            return None
        except Exception as e:
            print(f"✗ Błąd podczas pobierania {url}: {str(e)}")
            return None

async def pobierz_wiele_stron(lista_url):
    """Asynchronicznie pobiera dane z wielu stron."""
    async with aiohttp.ClientSession() as session:
        zadania = [ProfilDanych.pobierz_dane_async(session, url) for url in lista_url]
        wyniki = await asyncio.gather(*zadania, return_exceptions=True)
        
        prawidlowe_wyniki = [wynik for wynik in wyniki if wynik is not None and not isinstance(wynik, Exception)]
        return prawidlowe_wyniki

# Test asynchroniczny
async def test_async():
    """Testuje asynchroniczne pobieranie danych."""
    lista_testowa = [
        "https://ans-elblag.pl/",
        "https://www.python.org",
        "https://www.wikipedia.org",
        "https://www.github.com"
    ]
    
    start_time = time.time()
    wyniki = await pobierz_wiele_stron(lista_testowa)
    end_time = time.time()
    
    print(f"\n=== WYNIKI TESTÓW ===")
    print(f"Pobrano dane z {len(wyniki)} stron")
    print(f"Czas wykonania: {end_time - start_time:.2f}s")
    
    # Wyświetlenie przykładowych wyników
    for i, wynik in enumerate(wyniki[:2]):  # Tylko pierwsze 2 dla czytelności
        print(f"\n--- Strona {i+1} ---")
        print(f"URL: {wynik['url']}")
        print(f"Tytuł: {wynik['tytul']}")
        print(f"Emaile: {wynik['emaile']}")
        print(f"Telefony: {wynik['telefony']}")
        print(f"Informacje: {wynik['informacje'][:2]}")  # Tylko pierwsze 2

if __name__ == "__main__":
    # Test synchroniczny (oryginalny kod)
    print("=== TEST SYNCHRONICZNY ===")
    profil = ProfilDanych()
    print(f"Emaile: {profil.pobierz_email(soup)}")
    print(f"Adresy: {profil.pobierz_adresy(soup)}")
    print(f"Telefony: {profil.pobierz_telefony(soup)}")
    print(f"Informacje: {profil.pobierz_informacje(soup)}")
    
    # Test asynchroniczny
    print("\n=== TEST ASYNCHRONICZNY ===")
    asyncio.run(test_async())
