class Movie:
    def __init__(self, title, director, year):
        self.title = title
        self.director = director
        self.year = year

    def getTitle(self):
        return self.title
    def getDirector(self):
        return self.director
    def getYear(self):
        return self.year

class Series(Movie):
    def __init__(self, title, director, year, number_of_episodes, number_of_seasons):
        # Call the constructor of the parent class to initialize common attributes
        super().__init__(title, director, year)
        # Initialize the additional attribute
        self.number_of_episodes = number_of_episodes
        self.number_of_seasons = number_of_seasons

    def getNumberOfEpisodes(self):
        return self.number_of_episodes
    def getNumberOfSeasons(self):
        return self.number_of_seasons

