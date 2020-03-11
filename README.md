QuickDrawBattle
---------------
Choose the better drawing to find out the best drawings in the QuickDraw dataset.

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
You are given 2 random drawings of a random category and you choose which is better. The results are then sorted using [a lower bound of Wilson score confidence interval for a Bernoulli parameter](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html) and we can see the best ones!

Since there are so many drawings, it would take a long time for even one drawing to be voted on twice and we would probably never get results. For that reason, there is an 80% chance that you are given a drawing that has already been voted on. Otherwise at a 20% chance, you will be given a new drawing from the huge dataset.

Results
-------
You can see the results on the [ranking page](ranking). To get usable data, you can **GET** them from [/api/get\_ranking](/api/get_ranking). You probably want to get the key\_ids from here and find the strokes from the [full dataset](https://console.cloud.google.com/storage/quickdraw_dataset/full/binary). You can also get the strokes from here if you enable the strokes parameter, but they are in lists of coordinate pairs instead of 2 lists of x and y.

Parameters:
*   **category** - which [category](https://github.com/googlecreativelab/quickdraw-dataset/blob/master/categories.txt) the drawings will be from
*   **order** - use "ascending" to get ascending order
*   **strokes** - use "true" to get strokes in lists of strokes which are lists of coordinate pairs
*   **limit** - how many drawings to return, default 25, max 1000
*   **offset** - how many drawings to skip
*   **votemin** - the minimum amount of votes for a drawing

Example requests:
*   Get all sea turtles with at least 5 votes: [/api/get\_ranking?category=sea turtle&votemin=5](/api/get_ranking?category=sea turtle&votemin=5)
*   Get 100 drawings with strokes: [/api/get\_ranking?limit=100&strokes=true](/api/get_ranking?limit=100&strokes=true)
*   Skip the first 100 drawings and get 100 drawings: [/api/get\_ranking?offset=100&limit=100](/api/get_ranking?offset=100&limit=100)