class Movie:
    def __init__(self, title, director, genre, year, ratings):
        self.title: str = title
        self.director: str = director
        self.genre: str = genre
        self.year: str = year
        self.ratings: str = ratings
    def getTitle(self):
        return self.title
    def getDirector(self):
        return self.director
    def getGenre(self):
        return self.genre
    def getYear(self):
        return self.year
    def getRatings(self):
        return self.ratings

class Series(Movie):
    def __init__(self, title, director, genre, year, ratings, number_of_episodes, number_of_seasons):
        # Call the constructor of the parent class to initialize common attributes
        super().__init__(title, director, genre, year, ratings)
        # Initialize the additional attribute
        self.number_of_episodes: str = number_of_episodes
        self.number_of_seasons: str = number_of_seasons

    def getNumberOfEpisodes(self):
        return self.number_of_episodes
    def getNumberOfSeasons(self):
        return self.number_of_seasons

