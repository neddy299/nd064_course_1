import logging
import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# globals
metrics_db_connection = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global metrics_db_connection
    metrics_db_connection += 1

    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info(f'non-existing article "{post_id}", returning 404')
      return render_template('404.html'), 404
    else:
      app.logger.info(f'Article "{post["title"]}" retrieved!')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info(f'"About Us" page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.info(f'Article "{title}" created!')
            return redirect(url_for('index'))

    return render_template('create.html')

# Healthcheck endpoint
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    return response


# Metrics  endpoint
@app.route('/metrics')
def metrics():
    # Query database for posts count
    connection = get_db_connection()
    post_count = 0
    res_count_posts = connection.execute('SELECT count(*) FROM posts').fetchone()
    if res_count_posts is not None:
        post_count = res_count_posts[0]        
    connection.close()

    response = app.response_class(
            response=json.dumps({"db_connection_count":metrics_db_connection,"post_count":post_count}),
            status=200,
            mimetype='application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
    # Logging init
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
        datefmt='%m/%d/%Y, %H:%M:%S',
        handlers=[stdout_handler, stderr_handler]
        )

    app.run(host='0.0.0.0', port='3111')
