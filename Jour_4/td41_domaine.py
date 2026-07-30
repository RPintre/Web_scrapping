"""
TD 4.1 - Empreinte technique d'un domaine (OSINT).

Contexte du sujet : evaluer l'exposition technique d'un concurrent avant
une acquisition, a partir de sources 100% publiques (WHOIS, headers
HTTP, Certificate Transparency, robots.txt). Aucune authentification,
aucun bypass.

Usage :
    python td41_domaine.py doctolib.fr
    python td41_domaine.py ipssi.fr
"""

import json
import socket
import time
import warnings

import requests
import urllib3
import whois  # pip install python-whois

HEADERS = {"User-Agent": "IPSSI-OSINT (+r.pintre@gmail.com)"}

# On desactive volontairement la verif TLS en repli (voir analyse_headers) pour
# continuer a inspecter un site dont le certificat est invalide -- inutile
# d'etre averti a chaque fois que c'est fait expres.
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


def analyse_whois(domaine: str) -> dict:
    try:
        w = whois.whois(domaine)
        return {
            "registrar": str(w.registrar or "n/a"),
            "creation_date": str(w.creation_date or "n/a")[:10],
            "expiration_date": str(w.expiration_date or "n/a")[:10],
            "name_servers": list(set(w.name_servers or [])),
            "country": str(w.country or "n/a"),
        }
    except Exception as e:
        return {"erreur": str(e)}


def analyse_headers(domaine: str) -> dict:
    """HEAD sur le domaine. Si le certificat TLS ne verifie pas (vu en
    conditions reelles sur ipssi.fr), on le signale au lieu de planter :
    un certificat invalide est en soi une information d'exposition."""
    try:
        r = requests.head(f"https://{domaine}", headers=HEADERS, timeout=10, allow_redirects=True)
        certificat_valide = True
    except requests.exceptions.SSLError as e:
        try:
            r = requests.head(f"https://{domaine}", headers=HEADERS, timeout=10,
                               allow_redirects=True, verify=False)
            certificat_valide = False
        except Exception as e2:
            return {"erreur": str(e2)}
    except Exception as e:
        return {"erreur": str(e)}

    h = r.headers
    return {
        "status": r.status_code,
        "certificat_tls_valide": certificat_valide,
        "server": h.get("Server", "n/a"),
        "x_powered_by": h.get("X-Powered-By", "n/a"),
        "x_frame_options": h.get("X-Frame-Options", "n/a"),
        "csp_present": "Content-Security-Policy" in h,
        "hsts_present": "Strict-Transport-Security" in h,
    }


def sous_domaines_crtsh(domaine: str) -> list[str]:
    """Sous-domaines vus dans les journaux de certificats via l'API
    publique crt.sh. NB : ce service est un simple frontend Postgres
    public, notoirement lent/instable sous charge -- des timeouts sont
    frequents (observes en pratique sur ce TD, voir README), d'ou un
    timeout genereux et un vrai retry plutot qu'un simple try/except."""
    url = f"https://crt.sh/?q=%.{domaine}&output=json"
    derniere_erreur = None
    for tentative in range(2):
        try:
            r = requests.get(url, headers=HEADERS, timeout=45)
            r.raise_for_status()
            data = r.json()
            subs = list(set(
                entry["name_value"]
                for entry in data
                if "*" not in entry["name_value"] and entry["name_value"].endswith(domaine)
            ))
            return sorted(subs)[:100]
        except Exception as e:
            derniere_erreur = e
            time.sleep(2)
    return [f"ERREUR: {derniere_erreur}"]


def analyse_robots(domaine: str) -> str:
    try:
        r = requests.get(f"https://{domaine}/robots.txt", headers=HEADERS, timeout=10)
    except requests.exceptions.SSLError:
        try:
            r = requests.get(f"https://{domaine}/robots.txt", headers=HEADERS, timeout=10, verify=False)
        except Exception as e:
            return str(e)
    except Exception as e:
        return str(e)
    return r.text[:1000] if r.status_code == 200 else f"HTTP {r.status_code}"


def analyser_domaine(domaine: str) -> dict:
    print(f"[*] Analyse de {domaine}...")
    rapport = {
        "domaine": domaine,
        "ip": socket.gethostbyname(domaine) if domaine else "n/a",
        "whois": analyse_whois(domaine),
        "headers_http": analyse_headers(domaine),
        "sous_domaines": sous_domaines_crtsh(domaine),
        "robots_txt": analyse_robots(domaine),
    }
    rapport["nb_sous_domaines"] = len(
        [s for s in rapport["sous_domaines"] if not s.startswith("ERREUR")]
    )
    return rapport


if __name__ == "__main__":
    import sys

    domaine = sys.argv[1] if len(sys.argv) > 1 else "wikipedia.org"
    time.sleep(1)  # politesse
    rapport = analyser_domaine(domaine)
    sortie = f"rapport_{domaine}.json"
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"[+] Rapport sauvegarde : {sortie}")
    print(f"    {rapport['nb_sous_domaines']} sous-domaines trouves")
    print(f"    Serveur : {rapport['headers_http'].get('server', 'n/a')}")
    print(f"    Certificat TLS valide : {rapport['headers_http'].get('certificat_tls_valide', 'n/a')}")
