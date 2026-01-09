"""
TMDb (The Movie Database) API Script

Get your free API key from: https://www.themoviedb.org/settings/api
(Create account -> Settings -> API -> Request API Key -> Developer)
"""

import requests
import json

class MovieDatabase:
    def __init__(self, api_key):
        """
        Initialize with TMDb API key
        
        Args:
            api_key: Your TMDb API key (free from themoviedb.org)
        """
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        
    def search_movies(self, query, num_results=5):
        """
        Search for movies by title
        
        Args:
            query: Movie title to search for
            num_results: Number of results to return
        
        Returns:
            List of movie dictionaries with details
        """
        print(f"\n=== Searching for: {query} ===\n")
        
        try:
            # Search endpoint
            url = f"{self.base_url}/search/movie"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'en-US'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            print(f"Found {len(movies)} results\n")
            
            results = []
            for movie in movies[:num_results]:
                movie_id = movie['id']
                
                # Get detailed information
                details = self._get_movie_details(movie_id)
                
                if details:
                    movie_info = {
                        'id': movie_id,
                        'title': details.get('title', 'N/A'),
                        'year': details.get('release_date', 'N/A')[:4] if details.get('release_date') else 'N/A',
                        'rating': details.get('vote_average', 'N/A'),
                        'votes': details.get('vote_count', 0),
                        'runtime': details.get('runtime', 'N/A'),
                        'genres': [g['name'] for g in details.get('genres', [])],
                        'plot': details.get('overview', 'N/A'),
                        'budget': details.get('budget', 0),
                        'revenue': details.get('revenue', 0),
                        'imdb_id': details.get('imdb_id', 'N/A'),
                        'poster': f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get('poster_path') else 'N/A',
                        'url': f"https://www.themoviedb.org/movie/{movie_id}"
                    }
                    
                    # Get cast and crew
                    credits = self._get_movie_credits(movie_id)
                    if credits:
                        movie_info['directors'] = [c['name'] for c in credits.get('crew', []) if c.get('job') == 'Director']
                        movie_info['cast'] = [c['name'] for c in credits.get('cast', [])[:5]]
                    else:
                        movie_info['directors'] = []
                        movie_info['cast'] = []
                    
                    results.append(movie_info)
                    
                    # Print formatted output
                    self._print_movie_info(movie_info)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not connect to TMDb API: {e}")
            return []
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_titles(self, query, num_results=5):
        """
        Search for movies and TV series by title
        """
        print(f"\n=== Searching for movies & TV series: {query} ===\n")

        try:
            url = f"{self.base_url}/search/multi"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'en-US'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            print(f"Found {len(results)} results\n")

            output = []

            for item in results[:num_results]:
                media_type = item.get('media_type')

                if media_type == "movie":
                    details = self._get_movie_details(item['id'])
                    if not details:
                        continue

                    info = {
                        'type': 'movie',
                        'id': item['id'],
                        'title': details.get('title', 'N/A'),
                        'year': details.get('release_date', 'N/A')[:4] if details.get('release_date') else 'N/A',
                        'rating': details.get('vote_average', 'N/A'),
                        'votes': details.get('vote_count', 0),
                        'runtime': details.get('runtime', 'N/A'),
                        'genres': [g['name'] for g in details.get('genres', [])],
                        'plot': details.get('overview', 'N/A'),
                        'budget': details.get('budget', 0),
                        'revenue': details.get('revenue', 0),
                        'imdb_id': details.get('imdb_id', 'N/A'),
                        'poster': f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get('poster_path') else 'N/A',
                        'url': f"https://www.themoviedb.org/movie/{item['id']}"
                    }

                elif media_type == "tv":
                    details = self._get_tv_details(item['id'])
                    if not details:
                        continue

                    info = {
                        'type': 'tv',
                        'id': item['id'],
                        'title': details.get('name'),
                        'year': details.get('first_air_date', 'N/A')[:4],
                        'rating': details.get('vote_average'),
                        'seasons': details.get('number_of_seasons'),
                        'episodes': details.get('number_of_episodes'),
                        'genres': [g['name'] for g in details.get('genres', [])],
                        'plot': details.get('overview'),
                        'url': f"https://www.themoviedb.org/tv/{item['id']}"
                    }

                else:
                    continue

                output.append(info)

                self._print_media_info(info)

            return output

        except Exception as e:
            print(f"ERROR: {e}")
            return []

    
    def get_popular_movies(self, num_movies=10):
        """
        Get currently popular movies
        
        Args:
            num_movies: Number of movies to retrieve
        
        Returns:
            List of popular movies
        """
        print(f"\n=== Top {num_movies} Popular Movies ===\n")
        
        try:
            url = f"{self.base_url}/movie/popular"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'page': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            results = []
            for i, movie in enumerate(movies[:num_movies], 1):
                movie_info = {
                    'id': movie['id'],
                    'title': movie.get('title', 'N/A'),
                    'year': movie.get('release_date', 'N/A')[:4] if movie.get('release_date') else 'N/A',
                    'rating': movie.get('vote_average', 'N/A'),
                    'popularity': movie.get('popularity', 'N/A'),
                    'url': f"https://www.themoviedb.org/movie/{movie['id']}"
                }
                
                results.append(movie_info)
                
                print(f"{i}. {movie_info['title']} ({movie_info['year']}) - Rating: {movie_info['rating']}/10")
                print(f"   Popularity Score: {movie_info['popularity']}")
                print(f"   URL: {movie_info['url']}")
                print("-" * 60)
            
            return results
            
        except Exception as e:
            print(f"ERROR: {e}")
            return []
    
    def get_top_rated_movies(self, num_movies=10):
        """
        Get top rated movies of all time
        
        Args:
            num_movies: Number of movies to retrieve
        
        Returns:
            List of top rated movies
        """
        print(f"\n=== Top {num_movies} Rated Movies ===\n")
        
        try:
            url = f"{self.base_url}/movie/top_rated"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'page': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            movies = data.get('results', [])
            
            results = []
            for i, movie in enumerate(movies[:num_movies], 1):
                movie_info = {
                    'id': movie['id'],
                    'title': movie.get('title', 'N/A'),
                    'year': movie.get('release_date', 'N/A')[:4] if movie.get('release_date') else 'N/A',
                    'rating': movie.get('vote_average', 'N/A'),
                    'votes': movie.get('vote_count', 0),
                    'url': f"https://www.themoviedb.org/movie/{movie['id']}"
                }
                
                results.append(movie_info)
                
                print(f"{i}. {movie_info['title']} ({movie_info['year']}) - {movie_info['rating']}/10")
                print(f"   Votes: {movie_info['votes']:,}")
                print(f"   URL: {movie_info['url']}")
                print("-" * 60)
            
            return results
            
        except Exception as e:
            print(f"ERROR: {e}")
            return []
    
    def _get_movie_details(self, movie_id):
        """Get detailed information for a specific movie"""
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {'api_key': self.api_key, 'language': 'en-US'}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except:
            return None
    
    def _get_movie_credits(self, movie_id):
        """Get cast and crew for a specific movie"""
        try:
            url = f"{self.base_url}/movie/{movie_id}/credits"
            params = {'api_key': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except:
            return None
    
    def _get_tv_details(self, tv_id):
        """Get detailed information for a TV series"""
        try:
            url = f"{self.base_url}/tv/{tv_id}"
            params = {'api_key': self.api_key, 'language': 'en-US'}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()
        except:
            return None

    
    def _print_movie_info(self, movie_info):
        """Print formatted movie information"""
        print(f"Title: {movie_info['title']} ({movie_info['year']})")
        print(f"Rating: {movie_info['rating']}/10 ({movie_info['votes']:,} votes)")
        
        if movie_info['runtime'] != 'N/A':
            print(f"Runtime: {movie_info['runtime']} minutes")
        
        if movie_info['directors']:
            print(f"Directors: {', '.join(movie_info['directors'])}")
        
        if movie_info['cast']:
            print(f"Top Cast: {', '.join(movie_info['cast'])}")
        
        print(f"Genres: {', '.join(movie_info['genres'])}")
        print(f"Plot: {movie_info['plot']}")
        
        if movie_info['imdb_id'] != 'N/A':
            print(f"IMDb: https://www.imdb.com/title/{movie_info['imdb_id']}/")
        
        print(f"TMDb URL: {movie_info['url']}")
        print("=" * 80)
    
    def _print_media_info(self, media_info):
        """Print formatted movie or TV series information"""

        media_type = media_info.get("type", "movie")

        print(f"Title: {media_info['title']} ({media_info['year']})")
        print(f"Type: {media_type.upper()}")
        print(f"Rating: {media_info['rating']}/10")

        # ---- Movie-specific fields ----
        if media_type == "movie":
            if media_info.get("votes") is not None:
                print(f"Votes: {media_info['votes']:,}")

            if media_info.get("runtime") not in (None, 'N/A'):
                print(f"Runtime: {media_info['runtime']} minutes")

            if media_info.get("directors"):
                print(f"Directors: {', '.join(media_info['directors'])}")

        # ---- TV-specific fields ----
        elif media_type == "tv":
            if media_info.get("seasons") is not None:
                print(f"Seasons: {media_info['seasons']}")

            if media_info.get("episodes") is not None:
                print(f"Episodes: {media_info['episodes']}")

        # ---- Shared fields ----
        if media_info.get("cast"):
            print(f"Top Cast: {', '.join(media_info['cast'])}")

        if media_info.get("genres"):
            print(f"Genres: {', '.join(media_info['genres'])}")

        print(f"Plot: {media_info['plot']}")

        if media_info.get("imdb_id"):
            print(f"IMDb: https://www.imdb.com/title/{media_info['imdb_id']}/")

        print(f"TMDb URL: {media_info['url']}")
        print("=" * 80)



# Example usage
if __name__ == "__main__":
    print("TMDb Movie Database Script")
    print("=" * 80)
    print("\nTo use this script:")
    print("1. Go to: https://www.themoviedb.org/signup")
    print("2. Create a free account")
    print("3. Go to: https://www.themoviedb.org/settings/api")
    print("4. Request an API key (choose 'Developer' option)")
    print("5. Copy your API key and paste it below\n")
    print("=" * 80)
    
    # REPLACE WITH YOUR API KEY
    API_KEY = "037ff6ba26f3d5215cef3868aa3c8f73"
    

    # Initialize the database
    db = MovieDatabase(API_KEY)
    
    # Search for movies
    print("\n### SEARCHING FOR MOVIES ###")
    movies = db.search_movies("The Matrix", num_results=3)

    # Get popular movies
    print("\n\n### POPULAR MOVIES RIGHT NOW ###")
    popular = db.get_popular_movies(num_movies=5)
        
    # Get top rated movies
    print("\n\n### TOP RATED MOVIES OF ALL TIME ###")
    top_rated = db.get_top_rated_movies(num_movies=5)
        
    # Save results to JSON file (optional)
    if movies:
        with open('movie_results.json', 'w', encoding='utf-8') as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
        print("\n✅ Results saved to 'movie_results.json'")
    
    print("trallero trallalla")