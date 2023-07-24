import requests
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, SelectMultipleField
from wtforms.validators import DataRequired


def get_genre_id(genre):
    for id, gen in GENRE_IDS.items():
        if genre == gen:
            return id


GENRE_IDS = {
    "1": "Biography",
    "2": "Film Noir",
    "3": "Game Show",
    "4": "Musical",
    "5": "Sport",
    "6": "Short",
    "7": "Adult",
    "12": "Adventure",
    "14": "Fantasy",
    "16": "Animation",
    "18": "Drama",
    "27": "Horror",
    "28": "Action",
    "35": "Comedy",
    "36": "History",
    "37": "Western",
    "53": "Thriller",
    "80": "Crime",
    "99": "Documentary",
    "878": "Science Fiction",
    "9648": "Mystery",
    "10402": "Music",
    "10749": "Romance",
    "10751": "Family",
    "10752": "War",
    "10763": "News",
    "10764": "Reality",
    "10767": "Talk Show"
}
GENRES = []
for genre in GENRE_IDS.values():
    GENRES.append(genre)

STREAMING_SERVICES = ["Netflix", "Peacock", "Prime", "Disney", "Starz", "HBO", "Showtime", "Mubi", "Hulu", "Apple",
                      "Curiosity"]


def recommendation_search(services, genre, show_type, keyword):
    show_names = []
    streaming_names = []
    show_services = []
    poster_urls = []
    links = []
    overviews = []
    years = []

    first_search = True
    keep_searching = False

    while first_search:
        url = "https://streaming-availability.p.rapidapi.com/v2/search/basic"
        querystring = {"country": "us", "services": services,
                       "output_language": "en", "show_type": show_type, "genre": genre,
                       "show_original_language": "en", "keyword": keyword}

        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        results = response.json()
        for result in results["result"]:
            if result["streamingInfo"]:
                show_services.append(result["streamingInfo"]["us"])
            show_names.append(result["title"])
            overviews.append(result["overview"])
            if result["type"] == "movie":
                years.append(result["year"])
            else:
                years.append(result["firstAirYear"])
            if result["posterURLs"]:
                poster_urls.append(result["posterURLs"]["original"])
        if results["hasMore"]:
            keep_searching = True
        first_search = False
        next_cursor = results["nextCursor"]
        while keep_searching:
            querystring = {"country": "us", "services": services,
                           "output_language": "en", "show_type": show_type, "genre": genre,
                           "show_original_language": "en", "keyword": keyword, "cursor": next_cursor}
            response = requests.get(url, headers=headers, params=querystring)
            results = response.json()
            next_cursor = results["nextCursor"]
            for result in results["result"]:
                if result["streamingInfo"]:
                    show_services.append(result["streamingInfo"]["us"])
                show_names.append(result["title"])
                overviews.append(result["overview"])
                if result["type"] == "movie":
                    years.append(result["year"])
                else:
                    years.append(result["firstAirYear"])
                if result["posterURLs"]:
                    poster_urls.append(result["posterURLs"]["original"])
            if not results["hasMore"]:
                keep_searching = False
    for info in show_services:
        value = list(info.values())
        links.append(value[0][0]["link"])
        for keys, values in info.items():
            streaming_names.append(keys.title())
    return show_names, streaming_names, poster_urls, links, overviews, years


def find(title, type):
    url = "https://streaming-availability.p.rapidapi.com/v2/search/title"
    querystring = {"title": title, "country": "us", "show_type": type, "output_language": "en"}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    results = response.json()

    show_services = []
    titles = []
    overviews = []
    years = []
    poster_urls = []
    links = []
    streaming_names = []

    for result in results["result"]:
        if result["streamingInfo"]:
            show_services.append(result["streamingInfo"]["us"])
            titles.append(result["title"])
            overviews.append(result["overview"])
            if result["type"] == "movie":
                years.append(result["year"])
            else:
                years.append(result["firstAirYear"])
            if result["posterURLs"]:
                poster_urls.append(result["posterURLs"]["original"])

    for info in show_services:
        value = list(info.values())
        links.append(value[0][0]["link"])
        for keys, values in info.items():
            streaming_names.append(keys.title())
    return titles, streaming_names, overviews, years, poster_urls, links


class RecommendForm(FlaskForm):
    streaming_services = SelectMultipleField(label="Streaming Services (up to 4)", choices=STREAMING_SERVICES,
                                             validators=[DataRequired()])
    genre = SelectField(label="Genre", choices=GENRES, validators=[DataRequired()])
    show_type = SelectField(label="Type", choices=["Series", "Movie", "All"], validators=[DataRequired()])
    keyword = StringField(label="Keyword (Optional)")
    search = SubmitField(label="Search")


class SearchForm(FlaskForm):
    name = StringField(label="Title", validators=[DataRequired()])
    show_type = SelectField(label="Type", choices=["Series", "Movie", "All"], validators=[DataRequired()])
    search = SubmitField(label="Find")


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


@app.route("/", methods=["GET", "POST"])
def home():
    recommend_form = RecommendForm()
    search_form = SearchForm()

    if recommend_form.validate_on_submit():
        streaming_services = request.form.getlist("streaming_services")
        genre = recommend_form.genre.data
        show_type = recommend_form.show_type.data
        keyword = recommend_form.keyword.data
        if len(streaming_services) > 4:
            recommend_form.streaming_services.errors.append("Please select no more than 4 streaming services.")
        else:
            services = [service.lower() for service in streaming_services]
            titles, streaming_names, poster_urls, links, overviews, years = recommendation_search(services=services,
                                                                                                  genre=get_genre_id(
                                                                                                      genre),
                                                                                                  show_type=show_type.lower(),
                                                                                                  keyword=keyword)
            return render_template("recommendations.html", titles=titles, streaming_names=streaming_names,
                                   overviews=overviews, years=years, poster_urls=poster_urls, links=links)
        return render_template("home_page.html", recommend_form=recommend_form, search_form=search_form)

    if search_form.validate_on_submit():
        title = search_form.name.data
        type = search_form.show_type.data
        titles, streaming_names, overviews, years, poster_urls, links = find(title, type.lower())
        return render_template("find_results.html", recommend_form=recommend_form, search_form=search_form,
                               titles=titles, streaming_names=streaming_names, overviews=overviews, years=years,
                               poster_urls=poster_urls, links=links)
    return render_template("home_page.html", recommend_form=recommend_form, search_form=search_form)


if __name__ == '__main__':
    app.run(debug=True)
