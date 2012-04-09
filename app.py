from flask import Flask, request, make_response, redirect, render_template, flash
from flask import session as flask_session
from dropbox import client, session

app = Flask(__name__)

# API KEYs
APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'dropbox' # should be 'dropbox' or 'app_folder' as configured for your app

# Data structures
TOKEN_STORE = {}

def get_session():
    return session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

def get_client(access_token):
    sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return client.DropboxClient(sess)
    
def is_logged_in():
  if 'access_token_key' in flask_session:
    access_token_key = flask_session['access_token_key']
    if TOKEN_STORE.has_key(access_token_key):
      return True
  return False
  
def login_session(access_token):
  TOKEN_STORE[access_token.key] = access_token
  flask_session['access_token_key'] = access_token.key
  
  
def logout_session():
  access_token_key = flask_session['access_token_key']
  flask_session.pop('access_token_key', None)
  
  if TOKEN_STORE.has_key(access_token_key):
    del(TOKEN_STORE[access_token_key])
    
    
def get_access_token():
  access_token_key = flask_session['access_token_key']
  access_token = TOKEN_STORE.get(access_token_key)
  
  

# Routing stuff

@app.route("/")
def index():
  if not is_logged_in():
    flask_session.pop('access_token_key', None)
    
  return render_template('index.html')

@app.route("/callback")
def callback():
  oauth_token = request.args.get('oauth_token')
  request_token_key = oauth_token
  
  if not request_token_key:
    flash('Stop trying to hack the system!')
    return redirect('/')
  
  if not TOKEN_STORE.has_key(request_token_key):
    flash('Stop trying to hack the system!')
    return redirect('/')
      
  sess = get_session()
  
  request_token = TOKEN_STORE[request_token_key]
  access_token = sess.obtain_access_token(request_token)
  
  login_session(access_token)
  
  flash('You were logged in successfully, start uploading!')
  return redirect('/')

@app.route("/login")
def login():
  
  if is_logged_in():
    flash("you are Logged in")
    return redirect('/')
  
  # This is logging in through Dropbox
  sess = get_session()
  request_token = sess.obtain_request_token()
  TOKEN_STORE[request_token.key] = request_token
  callback = "%scallback" % (request.url_root)
  url = sess.build_authorize_url(request_token, oauth_callback=callback)
  return redirect(url)
  
@app.route("/upload", methods=['GET', 'POST'])
def upload():
  
  if not is_logged_in():
    flash('Please log in to continue')
    return redirect('/')
    
  access_token_key = flask_session['access_token_key']
  access_token = TOKEN_STORE.get(access_token_key)
    
  if request.method == 'POST':
    file = request.files['file']
    db = get_client(access_token)
    filename = file.filename
    result = db.put_file('/Public/' + filename, file.getvalue())
    
    dest_path = result['path']
    print dest_path
    path = "http://dl.dropbox.com/u/"+str(db.account_info()["uid"])+"/"+filename
    print path
    flash('File was uploaded successfully! Url is: %s'% path)
    return render_template('upload.html')
    
  else:
    return render_template('upload.html')
   
  
@app.route("/logout")
def logout():
  if not is_logged_in():
    flash('You were never logged in!')
    return redirect('/')
    
  logout_session()
  
  flash('You were logged out')
  return redirect('/')
  

if __name__ == "__main__":
  app.secret_key = 'some_secret_key'
  app.run()
    