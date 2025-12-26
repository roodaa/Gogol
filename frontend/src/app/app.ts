import { Component, signal, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { SearchService, SearchResponse, HealthResponse, IndexStats } from './services/search';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  // État de l'application
  title = signal('Gogol Search');
  query = signal('');
  searchResults = signal<SearchResponse | null>(null);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  // État de l'API
  healthStatus = signal<HealthResponse | null>(null);
  stats = signal<IndexStats | null>(null);

  constructor(private searchService: SearchService) {}

  ngOnInit() {
    // Vérifier le statut de l'API au chargement
    this.checkHealth();
    this.loadStats();
  }

  /**
   * Vérifie le statut de l'API
   */
  checkHealth() {
    this.searchService.getHealth().subscribe({
      next: (health) => {
        this.healthStatus.set(health);
      },
      error: (error) => {
        console.error('Erreur de connexion à l\'API:', error);
        this.healthStatus.set({
          status: 'error',
          message: 'Impossible de se connecter à l\'API. Assurez-vous qu\'elle est lancée.',
          index_ready: false
        });
      }
    });
  }

  /**
   * Charge les statistiques de l'index
   */
  loadStats() {
    this.searchService.getStats().subscribe({
      next: (stats) => {
        this.stats.set(stats);
      },
      error: (error) => {
        console.error('Erreur lors du chargement des stats:', error);
      }
    });
  }

  /**
   * Effectue une recherche
   */
  onSearch() {
    const q = this.query().trim();

    if (!q) {
      this.errorMessage.set('Veuillez entrer une requête');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.searchResults.set(null);

    this.searchService.search(q, 10).subscribe({
      next: (results) => {
        this.searchResults.set(results);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(
          'Erreur lors de la recherche. Assurez-vous que l\'API est lancée et que l\'index est créé.'
        );
        this.isLoading.set(false);
        console.error('Erreur de recherche:', error);
      }
    });
  }

  /**
   * Formate le score en pourcentage
   */
  formatScore(score: number): string {
    return (score * 100).toFixed(1) + '%';
  }
}
