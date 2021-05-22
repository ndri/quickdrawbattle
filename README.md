QuickDrawBattle
---------------
Choose the better drawing to find out the best drawings in the QuickDraw dataset. It is running at https://andri.io/quickdrawbattle/.

Made with:
* Python 3.7
* [Flask](https://palletsprojects.com/p/flask/)
* [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) and PostgreSQL
* [quickdraw](https://quickdraw.readthedocs.io/en/latest/)
* [VanillaJS](http://vanilla-js.com/)

About QuickDrawBattle
---------------------
Google collected over 50 million drawings with the game [Quick, Draw!](https://quickdraw.withgoogle.com/). They released [the dataset](https://github.com/googlecreativelab/quickdraw-dataset) for everyone to use, but most of the drawings are either incomplete or just bad. Let's sort out the best ones together and create a dataset of good drawings!

How does it work?
-----------------
You are given 2 random drawings of a random category and you choose which is better. The drawings are then sorted based on the votes and we can see the best ones!

Since there are so many drawings, it would take a long time for even one drawing to be voted on twice and we would probably never get usable results. For that reason, there are a maximum of 25 drawings up for battle per category. They will be replaced once they have been voted on 20 times. Some categories have more than 25 drawings right now, because there used to be no limit.

The score is calculated using [a lower bound of Wilson score confidence interval for a Bernoulli parameter](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html). During score calculation, every drawing gets one invisible win, so the score of drawings with no wins is not 0 and they can be compared. The scores are also normalized to a range from 0 to 1. [Table of all possible scores](https://andri.io/quickdrawbattle/static/scoring.png). 

Results
-------
You can see the results on the [ranking page](https://andri.io/quickdrawbattle/ranking). To get usable data, you can **GET** them from [/api/get\_ranking](https://andri.io/quickdrawbattle/api/get_ranking). You probably want to get the key\_ids from here and find the strokes from the [full dataset](https://console.cloud.google.com/storage/quickdraw_dataset/full/binary). You can also get the strokes from here if you enable the strokes parameter, but they are in lists of coordinate pairs instead of 2 lists of x and y.

Parameters:
*   **category** - which [category](https://github.com/googlecreativelab/quickdraw-dataset/blob/master/categories.txt) the drawings will be from
*   **order** - use "ascending" to get ascending order
*   **strokes** - use "true" to get strokes in lists of strokes which are lists of coordinate pairs
*   **limit** - how many drawings to return, default 25, max 1000
*   **offset** - how many drawings to skip
*   **votemin** - the minimum amount of votes for a drawing

Example requests:
*   Get all sea turtles with at least 5 votes: [/api/get\_ranking?category=sea turtle&votemin=5](https://andri.io/quickdrawbattle/api/get_ranking?category=sea%20turtle&votemin=5)
*   Get 100 drawings with strokes: [/api/get\_ranking?limit=100&strokes=true](https://andri.io/quickdrawbattle/api/get_ranking?limit=100&strokes=true)
*   Skip the first 100 drawings and get 100 drawings: [/api/get\_ranking?offset=100&limit=100](https://andri.io/quickdrawbattle/api/get_ranking?offset=100&limit=100)

Usage
-----

1. Clone this repo.
2. Set up postgresql and change the database uri in `app.cfg`.
3. `mkdir quickdraw_dataset_bin`
4. `gsutil -m cp "gs://quickdraw_dataset/full/binary/*.bin" quickdraw_dataset_bin` (warning, downloads 5+ GiB of quickdrawings)
   - If you don't have `gsutil`, install it using `curl https://sdk.cloud.google.com | bash` or [read here](https://cloud.google.com/storage/docs/gsutil_install).
   - If you have the dataset somewhere else, change the `dataset_dir` value in `config.ini`.
5. `python3 -m venv quickdrawbattleenv`
6. `source quickdrawbattleenv/bin/activate`
7. `pip3 install -r requirements.txt`
8. `python3 dbinit.py`
9. `python3 app.py`, serve with uwsgi and nginx ([guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-20-04)). 
