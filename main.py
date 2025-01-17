import numpy as np
import pickle
from flask import Flask, url_for, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
import base64
import tensorflow as tf
from PIL import Image 
import cv2
import io
from keras.models import load_model
import h5py
import wikipedia



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'gauravvermaa07076@gmail.com'
app.config['MAIL_PASSWORD'] = 'reiqgeaklkpiadxe'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
db = SQLAlchemy(app)
mail = Mail(app)


heart_model = pickle.load(open('model/heart_disease_model.pkl','rb'))
covid_model = load_model('model/covid.model')
liver_model = pickle.load(open('model/liver_model.pkl','rb'))
asd_model = pickle.load(open('model/asd_model.pkl','rb'))
diabetes_model = pickle.load(open('model/diabetes_model.pkl','rb'))


label_dict={0:'Covid19 Negative', 1:'Covid19 Positive'}
img_size = 100
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def init(self, username, password):
        self.username = username
        self.password = password


def predict(model,values,dic):
    values = np.asarray(values)
    return model.predict(values.reshape(1, -1))[0]


def preprocess(img):

	img=np.array(img)

	if(img.ndim==3):
		gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	else:
		gray=img

	gray=gray/255
	resized=cv2.resize(gray,(img_size,img_size))
	reshaped=resized.reshape(1,img_size,img_size)
	return reshaped

#url
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        global username
        if data: username = data.username
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('main'))
        return render_template('login.html', message="Incorrect Details! If not registered.. Please first do so!")

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            password=request.form['password']
            cpassword=request.form['cpassword']
            if password==cpassword:
                db.session.add(User(username=request.form['username'], password=request.form['password']))
                db.session.commit()
                return redirect(url_for('login'))
            
            else:
                return redirect(url_for('register'))

            
            
        except:
            return render_template('register.html', message="User Already Exists")
    else:
        return render_template('register.html')


@app.route('/main', methods=['GET', 'POST'])
def main():
    #render_template('main.html')
    if request.method == 'GET':
        return render_template("main.html")
        
    
    else:
        try:
            query = request.form['search']
            result = wikipedia.summary(query,sentences = 10)
            return render_template("main.html",result=result,query = query, pred = 1)
        
        except:
            query = request.form['search']
            message = "Your search - " + query + " did not match any document"
            return render_template("main.html",message=message)
             

@app.route('/heart_disease')
def heart():
    return render_template("heart.html")

@app.route('/liver_disese')
def liver():
    return render_template("liver.html")

@app.route("/covid")
def covid():
	return(render_template("covid.html"))

@app.route("/diabetes")
def diabetes():
	return(render_template("diabetes.html"))

@app.route("/ASD")
def ASD():
	return(render_template("ASD.html"))

    
@app.route("/predict_heart",methods= ['POST', 'GET'])
def predictPage_heart():
    try:
        if request.method == 'POST':
            to_predict_dict = request.form.to_dict()
            to_predict_list = list(map(float, list(to_predict_dict.values())))
            pred = predict(heart_model,to_predict_list, to_predict_dict)
            print(pred)
    except:
        message = "Please enter valid Data! You may have missed some data to be filled!"
        return render_template("heart.html", message = message)

    return render_template('predict_heart.html', pred = pred)

@app.route("/email_heart",methods= ['POST', 'GET'])
def email_heart_pos():
     if request.method=='POST':
        msg = Message("Heart_results",sender='medaware@demo.co',recipients=[username])
        msg.body = "Great! Your heart looks to be in great condition! Here is what you can do to continue having a healthy heart\n 1. Take a 10-minute walk. If you don't exercise at all, a brief walk is a great way to start.\n\n2. Give yourself a lift. Lifting a hardcover book or a two-pound weight a few times a day can help tone your arm muscles.\n\n3. Eat one extra fruit or vegetable a day.\n\n4. Make breakfast count. Start the day with some fruit and a serving of whole grains, like oatmeal, bran flakes, or whole-wheat toast.\n\n5. Have a handful of nuts. Walnuts, almonds, peanuts, and other nuts are good for your heart.\n\n6. Sample the fruits of the sea. Eat fish or other types of seafood instead of red meat once a week. It's good for the heart, the brain, and the waistline.\n\n7. Breathe deeply. Try breathing slowly and deeply for a few minutes a day. It can help you relax.\n\n8. Wash your hands often. Scrubbing up with soap and water often during the day is a great way to protect your heart and health. The flu, pneumonia, and other infections can be very hard on the heart.\n\n9. Count your blessings. Taking a moment each day to acknowledge the blessings in your life is one way to start tapping into other positive emotions. These have been linked with better health, longer life, and greater well-being, just as their opposites — chronic anger, worry, and hostility."     
        mail.send(msg)
        return render_template('predict_heart.html', pred = 0, message="Mail sent")

@app.route("/email_heart_neg",methods= ['POST', 'GET']) 
def email_heart_neg():
     if request.method=='POST':
          msg = Message("Heart_results",sender='medaware@demo.co',recipients=[username])
          msg.body = "Oopss!! There are chances you might be afflicted with a heart disease . Go get your clinical tests done and consult with your doctor asap. There is no need to panic. It is just a prediction which may be even be incorrect."
          mail.send(msg)
          return render_template('predict_heart.html', pred = 1, message="Mail sent")    

@app.route("/predict_liver",methods= ['POST', 'GET'])
def predictPage_liver():
    try:
        if request.method == 'POST':
            to_predict_dict = request.form.to_dict()
            to_predict_list = list(map(float, list(to_predict_dict.values())))
            pred = predict(liver_model,to_predict_list, to_predict_dict)
    except:
        message = "Please enter valid Data! You may have missed some data to be filled!"
        return render_template("liver.html", message = message)

    return render_template('predict_liver.html', pred = pred)

@app.route("/email_liver",methods= ['POST', 'GET'])
def email_liver_pos():
     if request.method=='POST':
        msg = Message("Liver_results",sender='medaware@demo.co',recipients=[username])
        msg.body = "GREAT! you are in good Health. Kudos! Your Liver seems healthy. You could follow the below suggestions for further"     
        mail.send(msg)
        return render_template('predict_liver.html', pred = 0, message="Mail sent")

@app.route("/email_liver_neg",methods= ['POST', 'GET']) 
def email_liver_neg():
     if request.method=='POST':
          msg = Message("Liver_results",sender='medaware@demo.co',recipients=[username])
          msg.body = "Oopss!! There are chances you might be afflicted with a liver disorder . Go get your clinical tests done and consult with your doctor asap. There is no need to panic. It is just a prediction which may be even be incorrect."
          mail.send(msg)
          return render_template('predict_liver.html', pred = 1, message="Mail sent") 

@app.route("/predict_ASD",methods= ['POST', 'GET'])
def predictPage_ASD():
    try:
        if request.method == 'POST':
            to_predict_dict = request.form.to_dict()
            print(to_predict_dict)
            to_predict_list = list(map(float, list(to_predict_dict.values())))
            print(to_predict_list)
            pred = predict(asd_model,to_predict_list, to_predict_dict)
    except:
        message = "Please enter valid Data! You may have missed some data to be filled!"
        return render_template("ASD.html", message = message)

    return render_template('predict_ASD.html', pred = pred)

@app.route("/email_asd",methods= ['POST', 'GET'])
def email_asd_pos():
     if request.method=='POST':
        msg = Message("Autisum Disorder results",sender='medaware@demo.co',recipients=[username])
        msg.body = "Great! Your look to be in great condition! Here is what you can do to avoid this disorder. \n\nLive healthy. Have regular check-ups, eat well-balanced meals, and exercise. \nMake sure you have good prenatal care, and take all recommended vitamins and supplements. \nDon’t take drugs during pregnancy. Ask your doctor before you take any medication. This is especially true for some anti-seizure drugs. \nAvoid alcohol. Say “no” to that glass of wine -- and any kind of alcoholic beverage -- while you’re pregnant. Seek treatment for existing health conditions. If you've been diagnosed with celiac disease or PKU, follow your doctor’s advice for keeping them under control. \nGet vaccinated. Make sure you get the German measles (rubella) vaccine before you get pregnant. It can prevent rubella-associated autism."     
        mail.send(msg)
        return render_template('predict_ASD.html', pred = 0, message="Mail sent")

@app.route("/email_asd_neg",methods= ['POST', 'GET']) 
def email_asd_neg():
     if request.method=='POST':
          msg = Message("Autisum Disorder results",sender='medaware@demo.co',recipients=[username])
          msg.body = "Oopss!! There are chances you might be suffering from Autism sprectrum disorder. Go get your clinical tests done and consult with your doctor asap. There is no need to panic. It is just a prediction which may be even be incorrect."
          mail.send(msg)
          return render_template('predict_ASD.html', pred = 1, message="Mail sent") 

@app.route("/predict_diabetes",methods= ['POST', 'GET'])
def predictPage_diabetes():
    try:
        if request.method == 'POST':
            to_predict_dict = request.form.to_dict()
            to_predict_list = list(map(float, list(to_predict_dict.values())))
            print(to_predict_list)
            pred = predict(diabetes_model,to_predict_list, to_predict_dict)
            print(pred)
    except:
        message = "Please enter valid Data! You may have missed some data to be filled!"
        return render_template("diabetes.html", message = message)

    return render_template('predict_diabetes.html', pred = pred)

@app.route("/email_diabetes",methods= ['POST', 'GET'])
def email_di_pos():
     if request.method=='POST':
        msg = Message("Diabetes_results",sender='medaware@demo.co',recipients=[username])
        msg.body = "Great! Your looks to be in great condition! Here is what you can do to continue being healthy heart\n 1. Take a 10-minute walk. If you don't exercise at all, a brief walk is a great way to start.\n\n2. Give yourself a lift. Lifting a hardcover book or a two-pound weight a few times a day can help tone your arm muscles.\n\n3. Eat one extra fruit or vegetable a day.\n\n4. Make breakfast count. Start the day with some fruit and a serving of whole grains, like oatmeal, bran flakes, or whole-wheat toast.\n\n5. Have a handful of nuts. Walnuts, almonds, peanuts, and other nuts are good for your heart.\n\n6. Sample the fruits of the sea. Eat fish or other types of seafood instead of red meat once a week. It's good for the heart, the brain, and the waistline.\n\n7. Breathe deeply. Try breathing slowly and deeply for a few minutes a day. It can help you relax.\n\n8. Wash your hands often. Scrubbing up with soap and water often during the day is a great way to protect your heart and health. The flu, pneumonia, and other infections can be very hard on the heart.\n\n9. Count your blessings. Taking a moment each day to acknowledge the blessings in your life is one way to start tapping into other positive emotions. These have been linked with better health, longer life, and greater well-being, just as their opposites — chronic anger, worry, and hostility."     
        mail.send(msg)
        return render_template('predict_diabetes.html', pred = 0, message="Mail sent")

@app.route("/email_diabetes_neg",methods= ['POST', 'GET']) 
def email_di_neg():
     if request.method=='POST':
          msg = Message("Heart_results",sender='medaware@demo.co',recipients=[username])
          msg.body = "Oopss!! There are chances you might be suffering from diabetes. Go get your clinical tests done and consult with your doctor asap. There is no need to panic. It is just a prediction which may be even be incorrect."
          mail.send(msg)
          return render_template('predict_diabetes.html', pred = 1, message="Mail sent") 

@app.route("/predict_covid", methods=["POST"])
def predict_covid():
	print('HERE')
	message = request.get_json(force=True)
	encoded = message['image']
	decoded = base64.b64decode(encoded)
	dataBytesIO=io.BytesIO(decoded)
	dataBytesIO.seek(0)
	image = Image.open(dataBytesIO)

	test_image=preprocess(image)

	prediction = covid_model.predict(test_image)
	result=np.argmax(prediction,axis=1)[0]
	accuracy=float(np.max(prediction,axis=1)[0])

	label=label_dict[result]

	print(prediction,result,accuracy)

	response = {'prediction': {'result': label,'accuracy': accuracy}}

	return jsonify(response)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")





if __name__ == '__main__':
    app.secret_key = "ThisIsNotASecret:p"
    with app.app_context():
        db.create_all()
        app.run(debug=True,port=5002)

# original requirment.txt
# absl-py==1.4.0
# astunparse==1.6.3
# beautifulsoup4==4.12.2
# blinker==1.6.2
# cachetools==5.3.0
# certifi==2022.12.7
# charset-normalizer==3.1.0
# click==8.1.3
# colorama==0.4.6
# contourpy==1.0.7
# cycler==0.11.0
# Cython==0.29.34
# distlib==0.3.6
# docopt==0.6.2
# filelock==3.9.0
# Flask==2.2.3
# Flask-Mail==0.9.1
# Flask-SQLAlchemy==3.0.3
# flatbuffers==23.3.3
# fonttools==4.39.3
# gast==0.4.0
# google-auth==2.16.2
# google-auth-oauthlib==1.0.0
# google-pasta==0.2.0
# greenlet==2.0.2
# grpcio==1.51.3
# h5py==3.9.0
# idna==3.4
# itsdangerous==2.1.2
# jax==0.4.6
# Jinja2==3.1.2
# joblib==1.2.0
# Js2Py==0.74
# keras==2.12.0
# kiwisolver==1.4.4
# libclang==15.0.6.1
# Markdown==3.4.1
# MarkupSafe==2.1.2
# matplotlib==3.7.1
# numpy==1.23.5
# oauthlib==3.2.2
# opencv-python==4.7.0.72
# opt-einsum==3.3.0
# packaging==23.0
# pandas==1.5.3
# Pillow==9.5.0
# pipwin==0.5.2
# platformdirs==3.1.1
# protobuf==4.22.1
# pyasn1==0.4.8
# pyasn1-modules==0.2.8
# pyjsparser==2.7.1
# pyparsing==3.0.9
# PyPrind==2.11.3
# pySmartDL==1.3.4
# python-dateutil==2.8.2
# pytz==2022.7.1
# pytz-deprecation-shim==0.1.0.post0
# requests==2.28.2
# requests-oauthlib==1.3.1
# rsa==4.9
# scikit-learn 
# scipy==1.10.1
# six==1.16.0
# soupsieve==2.4.1
# SQLAlchemy==2.0.13
# tensorboard==2.12.3
# tensorboard-data-server==0.7.0
# tensorflow==2.12.0
# tensorflow-estimator==2.12.0
# tensorflow-intel==2.12.0
# tensorflow-io-gcs-filesystem==0.31.0
# termcolor==2.3.0
# threadpoolctl==3.1.0
# typing_extensions==4.5.0
# tzdata==2023.3
# tzlocal==4.3
# urllib3==1.26.15
# Werkzeug==2.3.4
# wrapt==1.14.1