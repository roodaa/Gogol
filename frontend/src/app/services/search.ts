import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SearchResult {
  doc_id: number;
  title: string;
  url: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  processed_terms: string[];
  total_results: number;
  results: SearchResult[];
}

export interface HealthResponse {
  status: string;
  message: string;
  index_ready: boolean;
}

export interface IndexStats {
  total_documents: number;
  total_terms: number;
  total_postings: number;
  db_path: string;
  db_size_mb: number;
}

@Injectable({
  providedIn: 'root',
})
export class SearchService {
  private readonly apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  /**
   * Effectue une recherche via l'API
   */
  search(query: string, limit: number = 10): Observable<SearchResponse> {
    const params = { q: query, limit: limit.toString() };
    return this.http.get<SearchResponse>(`${this.apiUrl}/search`, { params });
  }

  /**
   * Vérifie le statut de l'API et de l'index
   */
  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.apiUrl}/health`);
  }

  /**
   * Récupère les statistiques de l'index
   */
  getStats(): Observable<IndexStats> {
    return this.http.get<IndexStats>(`${this.apiUrl}/stats`);
  }
}
