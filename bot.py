# -*- coding: utf-8 -*-
import time
import json
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    GREEN = Fore.GREEN + Style.BRIGHT
    RED = Fore.RED + Style.BRIGHT
    YELLOW = Fore.YELLOW + Style.BRIGHT
    CYAN = Fore.CYAN + Style.BRIGHT
    BLUE = Fore.BLUE + Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BLUE = RESET = ""

# --- CONFIGURATION API & TELEGRAM ---
TELEGRAM_TOKEN = "8356719393:AAHaNKKYG_W5ExbNYIM3M3Qp1N2uebqoLEE"
TELEGRAM_CHAT_ID = "7985193485"
INTERVALLE_VERIF = 60  # Temps d'attente entre chaque vérification globale

logging.basicConfig(level=logging.ERROR)

class AgentNotification:
    @staticmethod
    def envoyer_alerte(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except Exception:
            pass

SITES = [
    {"id": "1", "nom": "Espagne (BLS)", "url": "https://algeria.blsspainvisa.com/"},
    {"id": "2", "nom": "France (Capago)", "url": "https://fr-dz.capago.eu/fr/rendezvous/"},
    {"id": "3", "nom": "Italie (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/ita"},
    {"id": "4", "nom": "Belgique (TLScontact)", "url": "https://visas-be.tlscontact.com/en-us/country/dz/vac/dzALG2be"},
    {"id": "5", "nom": "Pays-Bas (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/nld/"},
    {"id": "6", "nom": "Autriche (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/aut/visa-type"},
    {"id": "7", "nom": "République Tchèque (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/cze/"},
    {"id": "8", "nom": "Pologne (Gov)", "url": "https://www.gov.pl/web/algerie/un-visa-schengen-type-c"},
    {"id": "9", "nom": "Malte (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/mlt/"},
    {"id": "10", "nom": "Allemagne (VFS)", "url": "https://visa.vfsglobal.com/dza/fr/deu/apply-visa"},
    {"id": "11", "nom": "Portugal (Ambassade)", "url": "https://argel.embaixadaportugal.mne.gov.pt/fr/section-consulaire/visa-fr"}
]

def mode_surveillance_automatique_12():
    print(f"\n{CYAN}🚀 Démarrage de la surveillance globale des 11 pays...{RESET}\n")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Mémoire de l'état précédent pour chaque site (False = fermé/inconnu, True = ouvert)
    dernier_etat_ouvert = {site["nom"]: False for site in SITES}

    while True:
        print(f"\n{BLUE}--- Cycle de vérification global à {time.strftime('%H:%M:%S')} ---{RESET}")
        for site in SITES:
            driver = None
            nom_site = site['nom']
            try:
                driver = webdriver.Chrome(options=options)
                driver.get(site["url"])
                time.sleep(3)
                
                page_text = driver.execute_script("return document.body.innerText;")
                page_lower = page_text.lower()
                mots_bloquants = ["complet", "fully booked", "no slots", "aucun rendez-vous", "fermé", "indisponible", "no appointments available"]
                est_ferme = any(mot in page_lower for mot in mots_bloquants)
                site_ok = len(page_text.strip()) > 100
                calendrier_ouvert = not est_ferme if site_ok else False
                
                statut_site_str = f"{GREEN}OK{RESET}" if site_ok else f"{RED}EN PANNE{RESET}"
                statut_cal_str = f"{GREEN}OUVERT / DISPONIBLE{RESET}" if calendrier_ouvert else f"{YELLOW}FERMÉ / COMPLET{RESET}"
                
                print(f"🌍 {nom_site} ➔ Site : [{statut_site_str}] | Calendrier : [{statut_cal_str}]")
                
                # CAS 1 : Le calendrier s'ouvre (et il était fermé avant)
                if site_ok and calendrier_ouvert:
                    if not dernier_etat_ouvert[nom_site]:
                        msg = f"🚨 *ALERTE : CRÉNEAUX DISPONIBLES !* \n🌍 Pays : *{nom_site}*\n🔗 [Accéder au site]({site['url']})"
                        AgentNotification.envoyer_alerte(msg)
                        dernier_etat_ouvert[nom_site] = True  # Mémorise qu'il est ouvert
                
                # CAS 2 : Le calendrier se ferme (et il était ouvert avant)
                else:
                    if dernier_etat_ouvert[nom_site]:
                        msg = f"🔒 *INFORMATION : Calendrier fermé / complet.* \n🌍 Pays : *{nom_site}*"
                        AgentNotification.envoyer_alerte(msg)
                        dernier_etat_ouvert[nom_site] = False  # Mémorise qu'il est fermé
                    
            except Exception as e:
                print(f"{RED}❌ Erreur sur {nom_site} : {e}{RESET}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass
            time.sleep(1)
            
        print(f"\n{CYAN}💤 Pause de {INTERVALLE_VERIF}s avant le prochain cycle...{RESET}")
        print("-" * 50)
        time.sleep(INTERVALLE_VERIF)

if __name__ == "__main__":
    mode_surveillance_automatique_12()