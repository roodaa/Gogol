"""
Web Crawler pour Gogol

Ce module implémente un crawler web qui:
1. Télécharge des pages HTML depuis des URLs
2. Extrait le contenu et les liens de ces pages
3. Suit les liens de manière récursive (breadth-first search)
4. Sauvegarde les données crawlées dans des fichiers
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import hashlib
from pathlib import Path
from typing import Set, List, Dict, Optional
import logging

from src.config import CRAWLER_CONFIG, RAW_DATA_DIR, LOG_CONFIG


class Crawler:
    """
    Classe principale du crawler web.

    Le crawler utilise une approche BFS (Breadth-First Search) pour parcourir
    les pages web de manière systématique, en respectant les limites configurées.
    """

    def __init__(self):
        """
        Initialise le crawler avec:
        - Un ensemble (set) pour tracker les URLs visitées (évite les doublons)
        - Une file d'attente (queue) pour les URLs à visiter
        - Configuration depuis CRAWLER_CONFIG
        - Logger pour tracer l'activité
        """
        # URLs déjà visitées (pour éviter de crawler 2 fois la même page)
        self.visited_urls: Set[str] = set()

        # URLs en attente de visite (file FIFO)
        self.urls_to_visit: List[str] = []

        # Configuration du crawler
        self.max_pages = CRAWLER_CONFIG["max_pages"]
        self.delay = CRAWLER_CONFIG["delay_between_requests"]
        self.timeout = CRAWLER_CONFIG["timeout"]
        self.user_agent = CRAWLER_CONFIG["user_agent"]

        # Compteur de pages crawlées
        self.pages_crawled = 0

        # Assurer que le dossier de données existe
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Configuration du logger
        self._setup_logger()

        self.logger.info("Crawler initialisé")

    def _setup_logger(self):
        """
        Configure le système de logging pour tracer l'activité du crawler.
        Les logs sont écrits dans un fichier et affichés dans la console.
        """
        self.logger = logging.getLogger("Gogol.Crawler")
        self.logger.setLevel(LOG_CONFIG["level"])

        # Handler pour fichier
        file_handler = logging.FileHandler(LOG_CONFIG["file"])
        file_handler.setLevel(logging.INFO)

        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """
        Vérifie si une URL est valide et appartient au même domaine.

        Args:
            url: L'URL à vérifier
            base_domain: Le domaine de base (pour rester sur le même site)

        Returns:
            True si l'URL est valide et du même domaine

        Explication:
            Pour éviter de crawler tout l'internet, on se limite au même domaine
            que l'URL de départ. On filtre aussi les URLs non-HTTP(S).
        """
        try:
            parsed = urlparse(url)

            # Vérifier que c'est bien HTTP ou HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False

            # Vérifier qu'on reste sur le même domaine
            if parsed.netloc != base_domain:
                return False

            # Ignorer certains types de fichiers
            ignored_extensions = ['.pdf', '.jpg', '.png', '.gif', '.zip', '.exe']
            if any(url.lower().endswith(ext) for ext in ignored_extensions):
                return False

            return True
        except Exception:
            return False

    def _fetch_page(self, url: str) -> Optional[requests.Response]:
        """
        Télécharge une page web avec gestion d'erreurs.

        Args:
            url: L'URL de la page à télécharger

        Returns:
            L'objet Response de requests, ou None en cas d'erreur

        Explication:
            - On utilise requests pour faire une requête HTTP GET
            - On ajoute un User-Agent pour s'identifier (bonne pratique)
            - On respecte un timeout pour éviter de bloquer indéfiniment
            - On gère les erreurs réseau courantes
        """
        try:
            headers = {
                'User-Agent': self.user_agent
            }

            self.logger.info(f"Fetching: {url}")
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            # Vérifier que la requête a réussi (status 200)
            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors du fetch de {url}: {e}")
            return None

    def _parse_page(self, response: requests.Response, url: str) -> Dict:
        """
        Parse le HTML et extrait les informations importantes.

        Args:
            response: La réponse HTTP contenant le HTML
            url: L'URL de la page (pour référence)

        Returns:
            Un dictionnaire contenant:
                - url: L'URL de la page
                - title: Le titre de la page
                - text: Le contenu textuel
                - links: Les liens trouvés sur la page
                - html: Le HTML brut (optionnel)

        Explication:
            BeautifulSoup permet de parser le HTML et d'en extraire
            facilement les éléments (titre, texte, liens).
        """
        soup = BeautifulSoup(response.content, 'lxml')

        # Extraire le titre
        title = soup.title.string if soup.title else "Sans titre"

        # Extraire le texte (en enlevant les scripts et styles)
        # get_text() extrait tout le texte visible de la page
        for script in soup(["script", "style"]):
            script.decompose()  # Retirer ces éléments

        text = soup.get_text(separator=' ', strip=True)

        # Extraire tous les liens
        links = []
        for link in soup.find_all('a', href=True):
            # urljoin gère les URLs relatives (ex: /about -> https://example.com/about)
            absolute_url = urljoin(url, link['href'])
            links.append(absolute_url)

        # Créer un hash unique pour identifier cette page
        page_hash = hashlib.md5(url.encode()).hexdigest()

        return {
            'url': url,
            'title': title,
            'text': text,
            'links': links,
            'hash': page_hash,
            'html': str(soup)  # HTML complet pour archivage
        }

    def _save_page(self, page_data: Dict):
        """
        Sauvegarde les données d'une page dans un fichier JSON.

        Args:
            page_data: Dictionnaire contenant les données de la page

        Explication:
            Chaque page est sauvegardée dans un fichier JSON séparé,
            nommé avec son hash MD5 pour unicité. Cela facilite
            l'indexation ultérieure.
        """
        filename = RAW_DATA_DIR / f"{page_data['hash']}.json"

        # On ne sauvegarde pas le HTML brut pour économiser de l'espace
        # (on peut le re-télécharger si besoin)
        data_to_save = {
            'url': page_data['url'],
            'title': page_data['title'],
            'text': page_data['text'],
            'links': page_data['links']
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Page sauvegardée: {filename}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")

    def crawl(self, start_url: str):
        """
        Lance le processus de crawling à partir d'une URL de départ.

        Args:
            start_url: L'URL de départ du crawling

        Algorithme:
            1. Ajouter l'URL de départ à la file d'attente
            2. Tant qu'il reste des URLs et qu'on n'a pas atteint max_pages:
                a. Prendre la prochaine URL
                b. La télécharger et la parser
                c. Sauvegarder les données
                d. Ajouter les nouveaux liens à la file
                e. Respecter le délai entre requêtes

        C'est un parcours BFS (Breadth-First Search):
            - On visite d'abord toutes les pages à distance 1
            - Puis toutes celles à distance 2, etc.
        """
        # Extraire le domaine de base pour rester sur le même site
        base_domain = urlparse(start_url).netloc

        # Ajouter l'URL de départ
        self.urls_to_visit.append(start_url)

        self.logger.info(f"Début du crawling depuis: {start_url}")
        self.logger.info(f"Domaine de base: {base_domain}")
        self.logger.info(f"Limite: {self.max_pages} pages")

        # Boucle principale du crawler
        while self.urls_to_visit and self.pages_crawled < self.max_pages:
            # Prendre la première URL de la file (FIFO)
            current_url = self.urls_to_visit.pop(0)

            # Skip si déjà visitée
            if current_url in self.visited_urls:
                continue

            # Marquer comme visitée
            self.visited_urls.add(current_url)

            # Télécharger la page
            response = self._fetch_page(current_url)
            if response is None:
                continue

            # Parser la page
            page_data = self._parse_page(response, current_url)

            # Sauvegarder les données
            self._save_page(page_data)

            # Incrémenter le compteur
            self.pages_crawled += 1
            self.logger.info(f"Progression: {self.pages_crawled}/{self.max_pages} pages")

            # Ajouter les nouveaux liens à la file
            for link in page_data['links']:
                if (link not in self.visited_urls and
                    link not in self.urls_to_visit and
                    self._is_valid_url(link, base_domain)):
                    self.urls_to_visit.append(link)

            # Respecter le délai entre requêtes (politesse + éviter le rate limiting)
            if self.urls_to_visit:  # Pas de délai après la dernière page
                time.sleep(self.delay)

        # Résumé final
        self.logger.info("=" * 50)
        self.logger.info("Crawling terminé!")
        self.logger.info(f"Pages crawlées: {self.pages_crawled}")
        self.logger.info(f"URLs visitées: {len(self.visited_urls)}")
        self.logger.info(f"URLs en attente: {len(self.urls_to_visit)}")
        self.logger.info(f"Données sauvegardées dans: {RAW_DATA_DIR}")
        self.logger.info("=" * 50)

        return {
            'pages_crawled': self.pages_crawled,
            'urls_visited': len(self.visited_urls),
            'urls_pending': len(self.urls_to_visit)
        }
