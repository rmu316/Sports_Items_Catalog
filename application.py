# Created by Richard Mu
# FSND Items Catalog Project
#
# Standard imports for SQL Alchemy Library,
# see http://flask.pocoo.org/docs/1.0/patterns/sqlalchemy/
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database_setup import Base, Category, User, Item
# Imports for login requests and then connecting with
# the 3rd party authentication system
from flask import session as login_session
import random
import string
import httplib2
import json
from flask import make_response
import requests
# Import all necessary libraries
from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash

app = Flask(__name__)


# GLOBAL VARIABLES #


# Facebook_auth URL
fb_ou = "https://graph.facebook.com/oauth/access_token?"
fb_et = "grant_type=fb_exchange_token&client_id="
cs = "&client_secret="
et = "&fb_exchange_token="


# Facebook user info URL
fb_ui = "https://graph.facebook.com/v3.2/me?"
at = "access_token="
fields = "&fields=name,id,email"


# Facebook user pic URL
fb_pi = "https://graph.facebook.com/v3.2/me/picture?"
fb_red = "&redirect=0&height=200&width=200"


# Facebook disconnect URL
fb_graph = "https://graph.facebook.com/"
perm = "/permissions?"


# INTERNAL METHODS #
# Used only by the server with no direct
# interaction with the user


# Connect to Database and create database session
def loadUpDB():
    engine = create_engine('sqlite:///itemcatalog.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


# Internal module to create a new User based on the login session
# Inputs: login session (includes user name, email, and picture)
# Outputs: the User ID, as determined by the User table
def createUser(login_session):
    session = loadUpDB()
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Return a User row from the User table, based on the primary key
# Inputs: User primary key
# Outputs: the entire User row as an object
def getUserInfo(user_id):
    session = loadUpDB()
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Returns a User primary key based on the user email provided
# Inputs: User email
# Outputs: User ID
def getUserID(email):
    try:
        session = loadUpDB()
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        # If we do not have a yet, we don't want an exception to be returned!
        return None


# EXTERNAL METHODS #
# Used to interface with the user through routing of
# webpages


# User Login page
# Inputs: none
# Outputs: an anti-forgery token
# Redirects: login.html
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Called by the login.html page, when the user hits 'Login to Facebook'
# Internal method to connect to Facebook Login, the 3rd party
# authentication/authorization service
# Inputs: methods used (POST)
# Outputs: HTML string of login outcome
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    # First, ensure that our login state is valid
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Receive the access token we got from login page
    access_token = request.data
    print "access token received %s " % access_token

    # Load up the fb_client_secrets.json file which we created with the unique
    # APP ID and secret from Facebook Login
    app_id = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    # First part of authentication protocol: exchange our APP ID and secret
    # and access token for a FB token
    url = fb_ou+fb_et+app_id+cs+app_secret+et+access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Looking at the output from the server token exchange, we now need to
    # extract the token by a number of splits
    #
    # First, split the result by commas and look at the first element only,
    # which gives the key:value pair
    split_by_commas = result.split(',')[0]
    # Second, split that result by colons, and consider only the second
    # element (the value)
    split_by_colons = split_by_commas.split(':')[1]
    # Now, as the token will consist of quotations, we need to replace those
    # remaining quotes with nothing so that we can directly paste this token
    # when we need it for future API calls to Facebook's OAuth service
    token = split_by_colons.replace('"', '')

    # With this token from Facebook, let's now grab the user info from FB
    url = fb_ui+at+token+fields
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Convert data to JSON
    data = json.loads(result)
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # We must store this token in the login session when we logout!
    login_session['access_token'] = token

    # Get user picture
    url = fb_pi+at+token+fb_red
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    # We now need to figure out if we need to create a new User row in the
    # User table or simply grab an existing User row from the table

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Now, we just create some HTML which we pass back to the login.html
    output = '''
        <h1>Welcome, %s!</h1>
        <img src='%s' style = 'width: 200px; height: 200px;
        border-radius: 100px; -webkit-border-radius: 100px;
        -moz-border-radius: 100px;'>''' % (
            login_session['username'],
            login_session['picture'])

    # Send a temporary popup message to the html saying that we've logged in!
    flash("Now logged in as %s" % login_session['username'])
    return output


# Called by the html pages, whenever the user hits the 'Logout'
# button at the top of the html page
# Internal method to disconnect the currently logged in user from
# Facebook Login
# Inputs: none
# Outputs: simply a flash update that the disconnection is successful
# Redirects: main page
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    # pass both the user's facebook it and access token to FB
    # in order to sucessfully delete this login session
    url = fb_graph+facebook_id+perm+at+access_token
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    # now we must delete all other aspects of the current login session
    # so that our web page views the user as having been "logged out"
    del login_session['facebook_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    flash("You've successfully logged out!")
    return redirect(url_for('showCatalog'))


# Method to pass a json object of ALL categories and items in our
# sports catalog database
# Inputs: none
# Outputs: a JSON object (convered from a Python Dictionary) of
# all categories, and the items in those categories
@app.route('/catalog.json')
def jsonEndpoint():
    session = loadUpDB()
    catalog = []
    categories = session.query(Category).all()
    for category in categories:
        cat = {}
        cat['id'] = category.id
        cat['name'] = category.name
        itemsInCat = []
        items = session.query(Item).filter_by(category_id=category.id).all()
        for item in items:
            it = {}
            it['cat_id'] = category.id
            it['description'] = item.desc
            it['id'] = item.id
            it['title'] = item.title
            itemsInCat.append(it)
        cat['Items'] = itemsInCat
        catalog.append(cat)
    return json.dumps(
        catalog,
        sort_keys=True,
        indent=4,
        separators=(',', ': '))


# Method to pass a json object of one SPECIFIC item in our catalog
# based on the category name and item of this item
# Inputs: none
# Outputs: a JSON object (using the serialize method in the setup.py) of
# the item which we want to know about
@app.route('/catalog.json/<string:category_name>/<string:item_name>')
def jsonEndpointItem(category_name, item_name):
    session = loadUpDB()
    item = {}
    theCategory = session.query(Category).filter_by(name=category_name).one()
    theItem = session.query(Item).filter_by(
        title=item_name,
        category_id=theCategory.id).one()
    return jsonify(item=theItem.serialize)


# Show all categories in Catalog
# Inputs: none
# Outputs: All category and item objects in our database
# Redirects: publicCatalog.html (if user is NOT logged in)
# or catalog.html (if user is logged in)
@app.route('/')
@app.route('/catalog')
def showCatalog():
    session = loadUpDB()
    categories = session.query(Category).all()
    items = session.query(Item).all()
    itemDict = {}
    # We build a dictionary of items to their corresponding
    # categories so that we can output them as "item (category)"
    for item in items:
        categoryName = session.query(Category).filter_by(
            id=item.category_id).one().name
        itemDict[item.title] = categoryName
    if 'username' not in login_session:
        return render_template(
            'publicCatalog.html',
            categories=categories,
            items=itemDict,
            session=login_session)
    else:
        return render_template(
            'catalog.html',
            categories=categories,
            items=itemDict)


# Create/add new item in Catalog
# Inputs: REST methods (GET or POST)
# Outputs: None
# Redirects: login.html (if user is NOT logged in)
# or catalog.html (if user is logged in)
# or newitem.html (if the user just accessed this site
# via a GET method call)
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    session = loadUpDB()
    # This is a user-privileged option. First
    # we check if a user has been logged in
    if 'username' not in login_session:
        flash('You must be logged in to add a new item')
        return redirect('/login')
    # If we are using this command as a POST method (in which we update with
    # new item info)
    if request.method == 'POST':
        # Ensure that ALL fields of the new item form are filled out!
        if (
            not request.form['title'] or not request.form['desc'] or
            not request.form['category']
        ):
            flash("You must have an input for all fields")
            return redirect('/catalog/new/')
        newItem = Item(
            title=request.form['title'],
            desc=request.form['desc'],
            category_id=int(request.form['category']),
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Item %s successfully created!' % newItem.title)
        return redirect(url_for('showCatalog'))
    # We are simply accessing this page in the first place (as a GET method)
    else:
        return render_template('newitem.html')


# Show all items in a single Category of the Catalog
# Inputs: category name
# Outputs: All category objects in our database,
# all item objects of a category, login session of user, size of items
# Redirects: publicCategory.html (if user is NOT logged in)
# or category.html (if user is logged in)
@app.route('/catalog/<string:category_name>/')
@app.route('/catalog/<string:category_name>/items/')
def showCategory(category_name):
    session = loadUpDB()
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    if 'username' not in login_session:
        # We pass the len(items) so we can display something like
        # (<category_name> (<number_of_items> items))
        # We also pass login_session so we can display the username
        # on the top right of the page
        return render_template(
            'publicCategory.html',
            items=items,
            category=category,
            categories=categories,
            size=len(items),
            session=login_session)
    else:
        return render_template(
            'category.html',
            items=items,
            category=category,
            categories=categories,
            size=len(items))


# Show details of a single itme in Catalog
# Inputs: category name, item name
# Outputs: Item object, session information, as well as the User object
# Redirects: publicItem.html or item.html, depending on whether the
# user is logged in or not
@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItem(category_name, item_name):
    session = loadUpDB()
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        category_id=category.id,
        title=item_name).one()
    creator = session.query(User).filter_by(id=item.user_id).one()
    # We must make sure
    # (1) authentication: A user is logged in
    # (2) authorization: the right user (i.e. the creator of this item)
    # is logged int in order for this item to be edited
    if (
        'username' not in login_session or
        item.user_id != login_session['user_id']
    ):
        return render_template(
            'publicItem.html',
            item=item,
            session=login_session,
            user=creator)
    else:
        return render_template('item.html', item=item, user=creator)


# Edit an item in the Catalog
# Inputs: Item name, methods GET and POST
# Outputs: None
# Redirects: main page (if an item is successfully edited) OR
# edititem.html (if the user simply accessed this page) OR
# /login page (if the user is not logged into the system)
@app.route('/catalog/<string:item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    session = loadUpDB()
    # Authentication: Is the user logged into the page?
    if 'username' not in login_session:
        flash('You must be logged in to edit an item')
        return redirect('/login')
    editedItem = session.query(Item).filter_by(title=item_name).one()
    # Authorization: Is the user that is logged in the correct one
    # (i.e. the creator) to edit this item?
    if editedItem.user_id != login_session['user_id']:
        flash('You do not have authorization to edit this item!')
        return redirect('/')
    # If we are updating an item and thus sending info to our database
    if request.method == 'POST':
        if (
            not request.form['title'] or not request.form['desc']
            or not request.form['category']
        ):
            flash("You must have an input for all fields")
            return redirect('/catalog/%s/edit' % editedItem.title)
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['desc']:
            editedItem.desc = request.form['desc']
        if request.form['category']:
            editedItem.category_id = int(request.form['category'])
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showCatalog'))
    # If we are simply accessing the edit Items page
    else:
        return render_template('edititem.html', item=editedItem)


# Delete an item from the Catalog
# Inputs: item name, methods GET and POST
# Outputs: All category and item objects in our database
# Redirects: login.html (if user is NOT logged in)
# or deleteitem.html (if the user is logged in and wants to delete an item)
# or main page (if user has already deleted the item)
@app.route('/catalog/<string:item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    session = loadUpDB()
    # Authentication: Is the user logged into the page?
    if 'username' not in login_session:
        flash('You must be logged in to delete an item')
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(title=item_name).one()
    # Authorization: Is the user that is logged in the correct one
    # (i.e. the creator) to edit this item?
    if itemToDelete.user_id != login_session['user_id']:
        flash('You do not have authorization to delete this item!')
        return redirect('/')
    # If we are updating an item via POST method
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCatalog'))
    # If we are trying to access the delete item page in the first place
    else:
        return render_template('deleteitem.html', item=itemToDelete)


# Main method
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
